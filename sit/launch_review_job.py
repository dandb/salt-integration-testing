#!/usr/bin/env python

from boto3.session import Session
from time import sleep
from sys import argv
import json
import logging
import os
import re
import yaml

from helpers.sit_helper import SITHelper
from helpers.log import Log
from helpers.cf_helper import CFHelper
from ecs_container import Container
from redis_client import RedisClient
from sit.check_sit import CheckSIT


class ReviewJob(object):

    BOTO_CLIENT_TYPE_ECS = 'ecs'
    BOTO_CLIENT_TYPE_EC2 = 'ec2'
    BOTO_CLIENT_TYPE_AUTOSCALING = 'autoscaling'
    TASK_FAILURE_REASON = 'RESOURCE'
    CONTAINER_INSTANCE_WAIT = 30
    CLUSTER_RESOURCE_WAIT = 60
    TASK_COMPLETION_WAIT = 30

    def __init__(self, job_name=None, build_number=None, master_ip=None, configs_directory=None, session=None):
        self.check_sit(configs_directory=configs_directory, session=session)
        sit_helper = SITHelper(configs_directory)
        self.configs_directory = configs_directory
        sit_configs = sit_helper.get_configs('sit')
        troposphere_configs = sit_helper.get_configs('troposphere')
        self.PROFILE = sit_configs['profile_name']
        self.LOGICAL_AUTOSCALING_GROUP_NAME = troposphere_configs['autoscaling_group_name']
        self.LOGICAL_CLUSTER_NAME = troposphere_configs['cluster_name']
        self.STACK_NAME = troposphere_configs['stack_name']
        self.ROLES = sit_helper.get_roles()
        self.ATTEMPT_LIMIT = sit_configs['attempt_limit']
        self.RESOURCES_ATTEMPT_LIMIT = sit_configs['resources_attempt_limit']
        self.INITIAL_CLUSTER_SIZE = sit_configs['initial_cluster_size']
        self.SAVE_LOGS = sit_configs['save_logs']
        self.HIGHSTATE_LOG_DIR = sit_configs['highstate_log_dir']
        self.REDIS_HOST = sit_configs.get('redis_host', None)
        self.cf_helper = CFHelper(configs_directory=configs_directory, session=session)
        self.family = self.join_items([job_name, build_number])
        self.master_ip = master_ip
        self.is_build_successful = True
        self.instance_was_launched = False
        self.instance_was_terminated = False
        self.init_boto_clients(session=session)
        self.cluster = self.get_cluster()
        self.autoscaling_group = self.get_autoscaling_group()
        self.running_task_ids = []

    def check_sit(self, configs_directory, session):
        CheckSIT(configs_directory=configs_directory, session=session).run()

    def init_boto_clients(self, session=None):
        if session is None:
            session = Session(profile_name=self.PROFILE)
        self.ecs_client = self.get_boto_client(session, self.BOTO_CLIENT_TYPE_ECS)
        self.autoscaling_client = self.get_boto_client(session, self.BOTO_CLIENT_TYPE_AUTOSCALING)
        self.ec2_client = self.get_boto_client(session, self.BOTO_CLIENT_TYPE_EC2)

    def run(self):
        self.prepare_cluster()
        tasks = self.register_tasks()
        self.start_tasks(tasks)
        self.wait_for_tasks_to_complete()

    def prepare_cluster(self):
        capacity = self.get_current_desired_capacity()
        logging.info('Current SIT Cluster capacity: {0}'.format(capacity))
        if capacity < self.INITIAL_CLUSTER_SIZE:
            logging.info('Cluster is currently empty or inadequate. Setting Desired Capacity to {0}'.format(
                self.INITIAL_CLUSTER_SIZE))
            self.set_current_desired_capacity(self.INITIAL_CLUSTER_SIZE)
        self.wait_for_first_instance()

    def scale_up_cluster(self):
        capacity = self.get_current_desired_capacity()
        new_cluster_size = capacity + self.INITIAL_CLUSTER_SIZE
        logging.info('Increasing Current SIT Cluster capacity from {0} to {1}'.format(capacity, new_cluster_size))
        self.set_current_desired_capacity(new_cluster_size)

    def wait_for_first_instance(self, attempt=1):
        if attempt > 10:
            self.error('Timed out waiting for instance to become available in sit cluster.')
        cluster_instances = self.ecs_client.list_container_instances(cluster=self.cluster)['containerInstanceArns']
        if not cluster_instances:
            logging.info('First instance not in cluster yet. Waiting for {0} seconds...'.format(self.CONTAINER_INSTANCE_WAIT))
            sleep(self.CONTAINER_INSTANCE_WAIT)
            self.wait_for_first_instance(attempt+1)
        else:
            self.display_instances_details(cluster_instances)

    def display_instances_details(self, cluster_instances):
        try:
            cluster_container_ids = map(lambda arn: arn.split('/')[1], cluster_instances)
            cluster_instance_details = self.ecs_client.describe_container_instances(
                containerInstances=cluster_container_ids, cluster=self.cluster)['containerInstances']
            cluster_instance_ids = map(lambda x: x['ec2InstanceId'], cluster_instance_details)
            logging.info('SIT Cluster Instance Ids: {0}'.format(cluster_instance_ids))
            self.display_instances_private_ips(cluster_instance_ids)
        except Exception as e:
            logging.warn('Failed to display instance private ip. Error: {0}'.format(e))

    def display_instances_private_ips(self, instance_ids):
        try:
            instance_reservations = self.ec2_client.describe_instances(InstanceIds=instance_ids)['Reservations']
            ips = [instance['PrivateIpAddress'] for reservation in instance_reservations for instance in reservation['Instances']]
            logging.info('SIT Cluster Instance IPs: {0}'.format(ips))
        except Exception as e:
            logging.warn('Failed to describe instance(s): {0}. Error: {1}'.format(instance_ids, e))

    def get_autoscaling_group(self):
        try:
            return self.cf_helper.get_resource_name(self.STACK_NAME, self.LOGICAL_AUTOSCALING_GROUP_NAME)
        except Exception as e:
            self.error('Unable to get the Autoscaling Group name', e)

    def register_tasks(self):
        tasks = []
        for role in self.ROLES:
            family = self.join_items([self.family, role])
            self.register_task(family, role)
            tasks.append(family)
        return tasks

    def register_task(self, family, role):
        try:
            self.ecs_client.register_task_definition(
                family=family,
                containerDefinitions=[self.get_container_definitions(role, family)]
            )
        except Exception as e:
            self.error('Failed to register tasks for family: {0}, role: {1}'.format(family, role), e)

    def get_container_definitions(self, role, family):
        container = Container(configs_directory=self.configs_directory, env='local', role=role, family=family, master_ip=self.master_ip, redis_host=self.REDIS_HOST)
        return container.get_container_definitions()

    def start_tasks(self, tasks):
        try:
            for task in tasks:
                response = self.attempt_start_task(task)
                logging.info('Task: {0} has started running..'.format(task))
                self.running_task_ids.append(response['tasks'][0]['taskArn'])
        except Exception as e:
            self.error('Failed to run tasks', e)

    def attempt_start_task(self, task, attempt=1, scaleup_required=True):
        if attempt > self.RESOURCES_ATTEMPT_LIMIT:
            self.error('Task {0} could not start. Timed out waiting for resources.'.format(task))
        response = self.ecs_client.run_task(
            cluster=self.cluster,
            taskDefinition=task
        )
        if response['failures'] and self.TASK_FAILURE_REASON in response['failures'][0]['reason']:
            logging.info('Task: {0} failed to start due to unavailable Resources. Waiting 60 seconds.'.format(task))
            if scaleup_required:
                self.scale_up_cluster()
            sleep(self.CLUSTER_RESOURCE_WAIT)
            response = self.attempt_start_task(task, attempt+1, scaleup_required=False)
        elif response['failures']:
            raise ValueError('Task: {0} failed to start due to unexpected reason:{1}'.format(
                task, response['failures'][0]['reason']))
        return response

    def wait_for_tasks_to_complete(self, attempt=0):
        if attempt > self.ATTEMPT_LIMIT:
            self.error('{0} attempts have gone by. Initiating termination sequence'.format(self.ATTEMPT_LIMIT))
        task_responses = self.get_task_responses()
        try:
            running_tasks = filter(lambda task: task['lastStatus'] != "STOPPED", task_responses)
            self.running_task_ids = map(lambda task: task['taskArn'], running_tasks)
            if running_tasks:
                logging.info('{0} Tasks are still running. Waiting for {1} seconds'.format(
                    len(self.running_task_ids), self.TASK_COMPLETION_WAIT))
                sleep(self.TASK_COMPLETION_WAIT)
                return self.wait_for_tasks_to_complete(attempt + 1)
        except Exception as e:
            self.error('Failed determining status of task', e)
        logging.info("Tasks are complete")

    def get_task_responses(self):
        try:
            return self.ecs_client.describe_tasks(cluster=self.cluster, tasks=self.running_task_ids)['tasks']
        except Exception as e:
            self.error('Failed to retrieve tasks from cluster.', e)

    def check_and_print_results(self):
        redis_client = RedisClient(self.REDIS_HOST)
        for role in self.ROLES:
            family = self.join_items([self.family, role])
            highstate_result = redis_client.get_highstate_result(family)
            try:
                logging.info('printing results for server: {0}'.format(role))
                parsed_result = json.loads(highstate_result)
                return_results = parsed_result.pop('return')
                json_results = json.dumps(parsed_result, indent=4)
                yaml_dump = yaml.safe_dump(return_results)
                logging.info('{0}\n{1}\n'.format(yaml_dump, json_results))
                if self.SAVE_LOGS:
                    self.check_for_log_dir()
                    self.write_to_log_file(yaml_dump, role)
                    self.write_to_log_file(json_results, role)
            except Exception as e:
                logging.info('Result:{0} Exception:{1}'.format(highstate_result, e))
            try:
                if self.highstate_failed(highstate_result):
                    self.is_build_successful = False
            except:
                self.is_build_successful = False

    def highstate_failed(self, result):
        try:
            possible_failures = ['"result": false', 'Data failed to compile:', 'Pillar failed to render with the following messages:']
            failures = [failure in result for failure in possible_failures]
            if True not in failures:
                failures = self.check_regex_failure(failures, result)
            return True in failures 
        except:
            logging.info('Error finding if there was a failure in the result')
            return True

    def check_regex_failure(self, failures, result):
        regex_failure = r"Rendering SLS '.*' failed:"
        failures.append(bool(re.search(regex_failure, result)))
        return failures

    def check_for_log_dir(self):
        if not os.path.exists(self.HIGHSTATE_LOG_DIR):
            os.makedirs(self.HIGHSTATE_LOG_DIR)

    def write_to_log_file(self, result, role):
        try:
            logging.info("Writing results to logs")
            with open('{0}/{1}.txt'.format(self.HIGHSTATE_LOG_DIR, role), 'a') as log_file:
                log_file.write(result)
        except Exception as e:
            self.error('Failed to write to logs', e)

    def fail_build_if_failures_exist(self):
        if not self.is_build_successful:
            self.error('build is not successful')

    def get_cluster(self):
        try:
            return self.cf_helper.get_resource_name(self.STACK_NAME, self.LOGICAL_CLUSTER_NAME)
        except Exception as e:
            self.error('Failed to retrieve the cluster', e)

    def set_current_desired_capacity(self, capacity=None):
        try:
            return self.autoscaling_client.set_desired_capacity(
                AutoScalingGroupName=self.autoscaling_group,
                DesiredCapacity=capacity
            )
        except Exception as e:
            self.error('Failed to increase the desired capacity for Autoscaling Group: {0}'.format(self.autoscaling_group), e)

    def get_current_desired_capacity(self):
        try:
            return self.autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.autoscaling_group]
            )['AutoScalingGroups'][0]['DesiredCapacity']
        except Exception as e:
            self.error('Failed to retrieve the desired capacity for Austoscaling Group: {0}.'.format(self.autoscaling_group), e)

    def get_boto_client(self, session, client_name):
        try:
            return session.client(client_name)
        except Exception as e:
            self.error('Failed to get boto client for: {0}'.format(client_name), e)

    def join_items(self, items=list(), delimeter='-'):
        try:
            return delimeter.join(items)
        except Exception as e:
            self.error('unable to join items: {0} with delimeter: {1}.'.format(items, delimeter), e)

    def terminate_running_tasks(self):
        task_definitions = []
        try:
            for task_id in self.running_task_ids:
                response = self.ecs_client.stop_task(task=task_id, cluster=self.cluster)
                task_definitions.append(response['task']['taskDefinitionArn'])
        except Exception as e:
            logging.error('Error occurred while terminating tasks.', e)
        finally:
            return task_definitions

    def error(self, message, e=None, error_code=2):
        terminated_tasks = self.terminate_running_tasks()
        logging.info('{0}. Exception: {1}\nFollowing tasks have been terminated: {2}'.format(
            message, e, terminated_tasks))
        exit(error_code)


def main():
    job = argv[1]
    build_number = argv[2]
    slave_ip = argv[3]
    configs_directory = argv[4]
    review_job = ReviewJob(job, build_number, slave_ip, configs_directory)
    review_job.run()
    review_job.check_and_print_results()
    review_job.fail_build_if_failures_exist()


if __name__ == '__main__':
    Log.setup()
    main()
