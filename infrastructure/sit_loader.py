#!/usr/bin/env python

import logging
from time import time

from helpers.log import Log
from helpers.cf_helper import CFHelper
from helpers.sit_helper import SITHelper
from sit_template import SITTemplate


class SITLoader(object):

    def __init__(self, configs_directory='configs', session=None):
        troposphere_configs = SITHelper(configs_directory).get_configs('troposphere')
        self.STACK_NAME = troposphere_configs['stack_name']
        self.TAG_VALUE = troposphere_configs['tag_value']
        self.AMI_ID = troposphere_configs['ami_id']
        self.SUBNET = troposphere_configs['subnet']
        self.SECURITY_GROUPS = troposphere_configs['security_groups']
        self.KEY_NAME = troposphere_configs['key_name']
        self.AMI_URL = troposphere_configs['ami_url']
        self.cf_helper = CFHelper(configs_directory=configs_directory, session=session)
        self.sit_template = SITTemplate(configs_directory)
        self.template = self.sit_template.template
        self.template_json = self.template.to_json()

    def validate_template(self):
        self.cf_helper.validate_template(self.template_json)

    def create_or_update_stack(self):
        if self.cf_helper.stack_exists(self.STACK_NAME):
            self.cf_helper.update_stack(self.STACK_NAME, self.template_json, self.TAG_VALUE)
        else:
            self.cf_helper.create_stack(self.STACK_NAME, self.template_json, self.TAG_VALUE)

    def stack_created_successfully(self):
        if not self.cf_helper.stack_was_created_successfully(self.STACK_NAME):
            Log.error('stack was not created')

    def run(self):
        start = time()
        self.validate_template()
        self.create_or_update_stack()
        self.stack_created_successfully()
        end = time()
        logging.info('Your stack is up and ready to go!')
        logging.info('Elapsed time: {0} seconds'.format(end - start))

if __name__ == '__main__':
    Log.setup()
    SITLoader().run()

