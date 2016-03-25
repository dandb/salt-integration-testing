#!/usr/bin/env python

import logging
from time import time

from helpers.log import Log
from helpers.cf_helper import CFHelper
from helpers.sit_helper import SITHelper
from sit_template import SITTemplate


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
        self.sit_template = SITTemplate()
        self.template = self.sit_template.template
        self.template_json = self.template.to_json()

    def validate_template(self):
        self.cf_helper.validate_template(self.template_json)

    def create_stack(self):
        self.cf_helper.create_stack(self.STACK_NAME, self.template_json, self.TAG_VALUE)

    def stack_created_successfully(self):
        if not self.cf_helper.stack_was_created_successfully(self.STACK_NAME):
            Log.error('stack was not created')

    def run(self):
        start = time()
        self.validate_template()
        self.create_stack()
        self.stack_created_successfully()
        end = time()
        logging.info('Your stack is up and ready to go!')
        logging.info('Elapsed time: {0} seconds'.format(end - start))

if __name__ == '__main__':
    Log.setup()
    SITLoader().run()

