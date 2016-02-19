#!/usr/bin/env python
import boto3
from boto3.session import Session
from TestServers import TestServers
from Container import Container
from RedisClient import RedisClient
from time import sleep
from sys import argv
import json
import yaml
import logging


class ReviewJob(object):

    ECS = 'ecs'
    EC2 = 'ec2'
    CONFIGS = TestServers.get_configs()
    PROFILE = CONFIGS['profile_name']
    AUTOSCALING = 'autoscaling'
    AUTOSCALING_GROUP_NAME = CONFIGS["autoscaling_group_name"]
    TEST_SERVERS = TestServers.get_server_names()
    ATTEMPT_LIMIT = CONFIGS['attempt_limit']
    CLUSTER_NAME = CONFIGS['cluster_name']

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

    def __init__(self, job_name=None, build_number=None, master_ip=None):
        self.family = self.join_items([job_name, build_number])
        self.master_ip = master_ip
        self.is_build_successful = True
        self.instance_was_launched = False
        self.instance_was_terminated = False
        self.instance = False
        self.init_boto_clients()
        self.cluster = self.get_cluster()
        self.autoscaling_group = self.get_autoscaling_group()
        self.init_instance()

    def init_boto_clients(self):
        session = Session(profile_name=self.PROFILE)
        self.ecs_client = self.get_boto_client(session, self.ECS)
        self.autoscaling_client = self.get_boto_client(session, self.AUTOSCALING)
        self.ec2_client = self.get_boto_client(session, self.EC2)

    def init_instance(self):
        current_instances = self.get_autoscale_instances()
        self.launch_instance()
        self.instance = self.get_launched_instance_name(current_instances)
        self.display_instance_private_ip()
        self.wait_for_instance_to_be_active()
        self.instance_arn = self.get_instance_arn_of_cluster_registered_instance()

    def display_instance_private_ip(self):
        try:
            instance_data = self.describe_instance([self.instance])
            private_ip = instance_data['Reservations'][0]['Instances'][0]['PrivateIpAddress']
            self.log.info('{0} private ip: {1}'.format(self.instance, private_ip))
        except Exception as e:
            self.log.warn('Failed to display instance private ip. Error: {0}'.format(e))

    def describe_instance(self, instance_ids):
        try:
            return self.ec2_client.describe_instances(InstanceIds=instance_ids)
        except Exception as e:
            self.log.warn('Failed to describe instance(s): {0}. Error: {1}'.format(instance_ids, e))

    def run(self):
        tasks = self.register_tasks()
        task_ids = self.start_tasks(tasks)
        self.wait_for_tasks_to_complete(task_ids)
        self.terminate_instance()
        self.check_and_print_results()
        self.fail_build_if_failures_exist()

    def get_autoscaling_group(self):
        try:
            autoscaling_groups = self.autoscaling_client.describe_auto_scaling_groups()['AutoScalingGroups']
            for autoscaling_group in autoscaling_groups:
                tags = autoscaling_group['Tags']
                for tag in tags:
                    if tag['Key'] == 'Name' and tag['Value'] == self.AUTOSCALING_GROUP_NAME:
                        return autoscaling_group['AutoScalingGroupName']
        except Exception as e:
            self.error('Unable to get the Autoscaling Group name', e)

    def wait_for_instance_to_be_active(self, attempt=0):
        if attempt > 30:
            self.error('Instance failed to become in service within 5 minutes.')
        sleep(10)
        instance = self.get_autoscale_instance()
        if not instance['LifecycleState'] == 'InService':
            self.log.info('Waiting 10 seconds for instance to become active')
            return self.wait_for_instance_to_be_active(attempt + 1)
        self.instance_was_launched = True

    def register_tasks(self):
        tasks = []
        for server in self.TEST_SERVERS:
            family = self.join_items([self.family, server])
            self.register_task(family, server)
            tasks.append(family)
        return tasks

    def register_task(self, family, server):
        try:
            self.ecs_client.register_task_definition(
                family=family,
                containerDefinitions=[self.get_container_definitions(server, family)]
            )
        except Exception as e:
            self.error('Failed to register tasks for family: {0}, server: {1}'.format(family, server), e)

    def get_container_definitions(self, server, family):
        container = Container(env='local', test_server=server, family=family, master_ip=self.master_ip)
        return container.get_container_definitions()

    def start_tasks(self, tasks):
        self.log.info('Starting tasks')
        try:
            task_ids = []
            for task in tasks:
                response = self.ecs_client.start_task(
                    cluster=self.cluster,
                    taskDefinition=task,
                    containerInstances=[self.instance_arn]
                )
                task_ids.append(response['tasks'][0]['taskArn'])
            return task_ids
        except Exception as e:
            self.error('Failed to run tasks', e)

    def wait_for_tasks_to_complete(self, task_ids, attempt=0):
        if attempt > self.ATTEMPT_LIMIT:
            self.error('{0} attempts have gone by. Initiating termination sequence'.format(self.ATTEMPT_LIMIT))
        task_responses = self.get_task_responses(task_ids)
        try:
            status = filter(lambda task: task['lastStatus'] != "STOPPED", task_responses)
            if status:
                self.log.info("Tasks are still running. Waiting for 30 seconds")
                sleep(30)
                return self.wait_for_tasks_to_complete(task_ids, attempt + 1)
        except Exception as e:
            self.error('Failed determining status of task', e)
        self.log.info("Tasks are complete")

    def get_task_responses(self, task_ids):
        try:
            return self.ecs_client.describe_tasks(cluster=self.cluster, tasks=task_ids)['tasks']
        except Exception as e:
            self.error('Failed to retrieve tasks from cluster.', e)

    def terminate_instance(self):
        if not self.instance_was_terminated:
            try:
                self.log.info('Terminating instance: {0}'.format(self.instance))
                self.autoscaling_client.terminate_instance_in_auto_scaling_group(
                    InstanceId=self.instance,
                    ShouldDecrementDesiredCapacity=True
                )
                self.log.info('Terminated instance: {0}'.format(self.instance))
                self.instance_was_terminated = True
            except Exception as e:
                self.log.info('Failed to terminate the instance: {0}. Decreasing desired instances. {1}'.format(self.instance, e))
                self.decrease_instance_count()
        else:
            self.log.info('Instance was terminated: {0}'.format(self.instance))

    def decrease_instance_count(self):
        try:
            current_count = self.get_current_desired_capacity()
            self.set_current_desired_capacity(current_count - 1)
            self.instance_was_terminated = True
        except Exception as e:
            self.error('Failed to decrease desired instance count', e)

    def check_and_print_results(self):
        redis_client = RedisClient()
        for server in self.TEST_SERVERS:
            family = self.join_items([self.family, server])
            highstate_result = redis_client.get_highstate_result(family)
            try:
                self.log.info('printing results for server: {0}'.format(server))
                parsed_result = json.loads(highstate_result)
                return_results = parsed_result.pop('return')
                print yaml.safe_dump(return_results), "\n"
                print json.dumps(parsed_result, indent=4), "\n"
            except:
                print highstate_result
            try:
                if self.highstate_failed(highstate_result):
                    self.is_build_successful = False
            except:
                self.is_build_successful = False

    def highstate_failed(self, result):
        try:
            possible_failures = ['"result": false', 'Data failed to compile:']
            failures = [failure in result for failure in possible_failures]
            return True in failures
        except:
            self.log.info('Error finding if there was a failure in the result')
            return True

    def fail_build_if_failures_exist(self):
        if not self.is_build_successful:
            self.error('build is not successful')

    def get_cluster(self):
        clusters = self.ecs_client.list_clusters()
        cluster_arns = clusters['clusterArns']
        for cluster_arn in cluster_arns:
            if self.CLUSTER_NAME in cluster_arn:
                return cluster_arn

    def launch_instance(self):
        self.log.info('Launching instance')
        self.set_current_desired_capacity(self.get_current_desired_capacity() + 1)

    def set_current_desired_capacity(self, capacity=None):
        try:
            return self.autoscaling_client.set_desired_capacity(
                AutoScalingGroupName=self.autoscaling_group,
                DesiredCapacity=capacity
            )
        except Exception as e:
            self.error('Failed to increase the desired capacity for Autoscaling Group: {0}'.format(self.autoscaling_group), e)

    def get_launched_instance_name(self, current_instances, attempt=0, wait=0):
        if attempt >= 30:
            self.error('instance failed to launch within 5 minutes. You may have a hanging instance')
        sleep(wait)
        all_instances = self.get_autoscale_instances()
        # Check if new instance has actually launched. Call function recursively until new instance begins provisioning
        new_instance = [instance for instance in all_instances if instance not in current_instances]
        if not new_instance:
            self.log.info('No new instance found. Waiting 10 seconds before checking again')
            return self.get_launched_instance_name(current_instances, attempt + 1, 10)
        self.log.info('New instance has launched: {0}'.format(new_instance))
        return new_instance[0]

    def get_instance_arn_of_cluster_registered_instance(self, wait=60):
        self.log.info("Waiting {0} seconds before checking if new instance is in the cluster".format(wait))
        sleep(wait)
        cluster_instances = self.get_cluster_instances()
        cluster_has_instance = self.cluster_has_instance(cluster_instances)
        if cluster_instances and cluster_has_instance:
            self.log.info("Instance successfully registered into cluster")
            return cluster_has_instance[0]
        self.log.info("New instance not in cluster yet. Must give it another shot...")
        return self.get_instance_arn_of_cluster_registered_instance(30)

    def get_current_desired_capacity(self):
        try:
            return self.autoscaling_client.describe_auto_scaling_groups(
                AutoScalingGroupNames=[self.autoscaling_group]
            )['AutoScalingGroups'][0]['DesiredCapacity']
        except Exception as e:
            self.error('Failed to retrieve the desired capacity for Austoscaling Group: {0}.'.format(self.autoscaling_group), e)

    def get_autoscale_instance(self):
        try:
            return self.autoscaling_client.describe_auto_scaling_instances(InstanceIds=[self.instance])['AutoScalingInstances'][0]
        except Exception as e:
            self.error('Failed to get list of all autoscale instances', e)

    def get_autoscale_instances(self):
        try:
            instances = self.autoscaling_client.describe_auto_scaling_instances()['AutoScalingInstances']
            return [instance['InstanceId'] for instance in instances if instance['AutoScalingGroupName'] == self.autoscaling_group and instance['LifecycleState'] != 'Terminating']
        except Exception as e:
            self.error('Failed to get list of all autoscale instances', e)

    def get_cluster_instances(self):
        try:
            return self.ecs_client.list_container_instances(cluster=self.cluster)['containerInstanceArns']
        except Exception as e:
            self.error('Failed to retrieve all instances within cluster: {0}'.format(self.cluster), e)

    def cluster_has_instance(self, all_instances):
        try:
            if not all_instances:
                return False
            cluster_instances = self.ecs_client.describe_container_instances(
                cluster=self.cluster,
                containerInstances=all_instances
            )['containerInstances']
            return [instance['containerInstanceArn'] for instance in cluster_instances if instance['ec2InstanceId'] == self.instance]
        except Exception as e:
            self.error('Failed to determine if instance is registered to cluster: {0}'.format(self.cluster), e)

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

    def error(self, message, e=None, error_code=2):
        self.log.info('{0}. Exception: {1}'.format(message, e))
        if self.instance_was_launched:
            self.terminate_instance()
        exit(error_code)

def main():
    job = argv[1]
    build_number = argv[2]
    slave_ip = argv[3]
    review_job = ReviewJob(job, build_number, slave_ip)
    review_job.run()

if __name__ == '__main__':
    main()
