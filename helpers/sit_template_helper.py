#!/usr/bin/env python

import logging
import subprocess

from helpers.cf_helper import CFHelper
from helpers.ec2_helper import EC2Helper
from helpers.sit_helper import SITHelper
from helpers.log import Log


class SITTemplateHelper(object):
    
    def __init__(self, session=None, configs_directory='configs'):
        self.configs = SITHelper(configs_directory).get_configs('troposphere')
        self.STACK_NAME = self.configs['stack_name']
        self.KEY_NAME = self.configs['key_name']
        self.AMI_ID = self.configs['ami_id']
        self.AMI_URL = self.configs['ami_url']
        self.SECURITY_GROUPS = self.configs['security_groups']
        self.SUBNET = self.configs['subnet']
        self.cf_helper = CFHelper(session)
        self.ec2_helper = EC2Helper(session)
    
    def validate_stack_exists(self):
        if self.cf_helper.stack_exists(self.STACK_NAME):
            Log.error('The stack "{0}" already exists'.format(self.STACK_NAME))

    def validate_configs(self):
        logging.info('Validating configs')
        missing_configs = [config for config, value in self.configs.iteritems() if value is None]
        if missing_configs:
            Log.error('The following configs have not been added in configs/troposphere.yml: {0}'.format(missing_configs))

    def validate_aws_resources(self):
        logging.info('Validating AWS resources exist')
        if not self.ec2_helper.describe_key_pairs([self.KEY_NAME]):
            self.not_found_error('Key pair', self.KEY_NAME)
        if not self.ec2_helper.describe_images([self.AMI_ID]):
            self.open_url(self.AMI_URL)
            self.not_found_error('AMI ID', self.KEY_NAME)
        if not self.ec2_helper.describe_security_groups(self.SECURITY_GROUPS):
            self.not_found_error('Security Groups', self.SECURITY_GROUPS)
        if not self.ec2_helper.describe_subnets([self.SUBNET]):
            self.not_found_error('Subnet', self.SUBNET)

    def open_url(self, url):
        subprocess.call(['open', url])

    def not_found_error(self, resource_name, resource):
        Log.error('{0} "{1}" not found. Please update configs/troposphere.yml'.format(resource_name, resource))

    def validate(self):
        self.validate_stack_exists()
        self.validate_configs()
        self.validate_aws_resources()
    

if __name__ == '__main__':
    SITTemplateHelper().validate()
