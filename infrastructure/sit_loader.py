#!/usr/bin/env python

import logging
import time

from helpers.log import Log
from helpers.cf_helper import CFHelper
from helpers.ec2_helper import EC2Helper
from helpers.sit_helper import SITHelper


class SITLoader(object):

    TROPOSPHERE_CONFIGS = SITHelper.get_configs('troposphere')
    STACK_NAME = TROPOSPHERE_CONFIGS['stack_name']
    TAG_VALUE = TROPOSPHERE_CONFIGS['tag_value']
    AMI_ID = TROPOSPHERE_CONFIGS['ami_id']
    SUBNET = TROPOSPHERE_CONFIGS['subnet']
    SECURITY_GROUPS = TROPOSPHERE_CONFIGS['security_groups']
    KEY_NAME = TROPOSPHERE_CONFIGS['key_name']
    AMI_URL = TROPOSPHERE_CONFIGS['ami_url']

    def __init__(self):
        self.cf_helper = CFHelper()
        self.ec2_helper = EC2Helper()
        self.validate_stack_exists()
        self.validate_configs()
        self.validate_aws_resources()
        from sit_template import SITTemplate
        self.sit_template = SITTemplate()
        self.template = self.sit_template.template
        self.template_json = self.template.to_json()

    def validate_stack_exists(self):
        if self.cf_helper.stack_exists(self.STACK_NAME):
            Log.error('The stack "{0}" already exists'.format(self.STACK_NAME))

    def validate_configs(self):
        logging.info('Validating configs')
        missing_configs = [config for config, value in self.TROPOSPHERE_CONFIGS.iteritems() if value is None]
        if missing_configs:
            Log.error('The following configs have not been added in configs/troposphere.yml: {0}'.format(missing_configs))

    def validate_aws_resources(self):
        logging.info('Validating AWS resources exist')
        if not self.ec2_helper.describe_key_pairs([self.KEY_NAME]):
            self.not_found_error('Key pair', self.KEY_NAME)
        if not self.ec2_helper.describe_images([self.AMI_ID]):
            subprocess.call(['open', self.AMI_URL])
            self.not_found_error('AMI ID', self.KEY_NAME)
        if not self.ec2_helper.describe_security_groups(self.SECURITY_GROUPS):
            self.not_found_error('Security Groups', self.SECURITY_GROUPS)
        if not self.ec2_helper.describe_subnets([self.SUBNET]):
            self.not_found_error('Subnet', self.SUBNET)

    def not_found_error(self, resource_name, resource):
        Log.error('{0} "{1}" not found. Please update configs/troposphere.yml'.format(resource_name, resource))

    def validate_template(self):
        self.cf_helper.validate_template(self.template_json)

    def create_stack(self):
        self.cf_helper.create_stack(self.STACK_NAME, self.template_json, self.TAG_VALUE)

    def stack_created_successfully(self):
        if not self.cf_helper.stack_was_created_successfully(self.STACK_NAME):
            Log.error('stack was not created')

    def run(self):
        start = time.time()
        self.validate_template()
        self.create_stack()
        self.stack_created_successfully()
        end = time.time()
        logging.info('Your stack is up and ready to go!')
        logging.info('Elapsed time: {0} seconds'.format(end - start))

if __name__ == '__main__':
    Log.setup()
    SITLoader().run()

