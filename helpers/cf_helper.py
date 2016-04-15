#!/usr/bin/env python

import time
import logging
from boto3.session import Session

from helpers.sit_helper import SITHelper
from helpers.log import Log


class CFHelper(object):

    FAILED_STATES = ['CREATE_FAILED', 'DELETE_FAILED', 'DELETE_COMPLETE']
    COMPLETE_STATES = ['CREATE_COMPLETE']

    def __init__(self, configs_directory='configs', session=None):
        if session is None:
            sit_configs = SITHelper(configs_directory).get_configs('sit')
            session = Session(profile_name=sit_configs['profile_name'])
        self.cf_client = session.client('cloudformation')

    def validate_template(self, template_body):
        logging.info('Validating template')
        try:
            self.cf_client.validate_template(TemplateBody=template_body)
        except Exception as e:
            Log.error('stack validation error', e)

    def create_stack(self, stack_name, template_body, tag_value):
        logging.info('Creating stack: {0}'.format(stack_name))
        try:
            self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                OnFailure='DELETE',
                Capabilities=['CAPABILITY_IAM'],
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': tag_value 
                    }
                ]    
            )['StackId']
        except Exception as e:
            Log.error('Failed to create stack {0}'.format(stack_name), e)
            
    def stack_exists(self, stack_name):
        return self.get_stack_info(stack_name)

    def stack_was_created_successfully(self, stack_name, attempt=1, sleep_time=20):
        if attempt > 25:
            logging.info('Stack was not created in the alotted time')
            return False
        try:
            stack_info = self.get_stack_info(stack_name)
            stack_status = stack_info['StackStatus']
            if stack_status in self.COMPLETE_STATES:
                return True
            if stack_status in self.FAILED_STATES:
                return False
        except Exception as e:
            logging.info('There was a problem checking status of stack: {0}'.format(e))
        logging.info('Stack creation still in progress. Waiting {0} seconds'.format(sleep_time))
        time.sleep(sleep_time)
        return self.stack_was_created_successfully(stack_name, attempt+1)

    def get_stack_info(self, stack_name):
        try:
            return self.cf_client.describe_stacks(StackName=stack_name)['Stacks'][0]
        except Exception as e:
            logging.info('stack info not found for: {0}. Error: {1}'.format(stack_name, e))
            return False 

    def get_resource_name(self, stack_name, logical_name):
        try:
            return self.cf_client.describe_stack_resource(
                StackName=stack_name, 
                LogicalResourceId=logical_name
            )['StackResourceDetail']['PhysicalResourceId']
        except Exception as e:
            Log.error('resource {0} in stack {1} not found'.format(logical_name, stack_name), e)
