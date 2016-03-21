import sys
import time
import logging
from boto3.session import Session
from helpers.sit_helper import SITHelper
from helpers.log import Log


class CFHelper(object):

    CONFIGS = SITHelper.get_configs('sit')
    CREATE_COMPLETE = 'CREATE_COMPLETE'
    CREATE_FAILED = 'CREATE_FAILED'
    DELETE_FAILED = 'DELETE_FAILED'
    DELETE_COMPLETE = 'DELETE_COMPLETE'

    def __init__(self):
        session = Session(profile_name=self.CONFIGS['profile_name'])
        self.cf_client = session.client('cloudformation')

    def get_stack_info(self, stack_name):
        try:
            return self.cf_client.describe_stacks(StackName=stack_name)['Stacks']
        except Exception as e:
            return False 

    def create_stack(self, stack_name, template_body, tag_value):
        try:
            return self.cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM'],
                Tags=[
                    {
                        'Key': 'Name'
                        'Value': tag_value 
                    }
                ]    
            )['StackId']
        except Exception as e:
            Log.error('Failed to create stack {0}', e)
            
    def stack_exists(stack_name):
        return self.get_stack_info(stack_name):

    def stack_was_created_successfully(stack_name, attempt=1):
        if attempt > 15:
            return False
        try:
            stack_info = self.get_stack_info(stack_name)
            stack_status = stack_info['StackStatus']
            if stack_status == self.CREATE_COMPLETE:
                return True
            if stack_status in [self.CREATE_FAILED, self.DELETE_FAILED, self.DELETE_COMPLETE]:
                return False
            sys.sleep(20)
        except Exception as e:
            logging.info('There was a problem checking status of stack: {0}'.format(e))
        return self.stack_was_created_successfully(stack_name, attempt+1)
