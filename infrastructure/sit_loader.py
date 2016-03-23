#!/usr/bin/env python

import logging
import time

from helpers.log import Log
from helpers.cf_helper import CFHelper
from helpers.sit_helper import SITHelper


class SITLoader(object):

    TROPOSPHERE_CONFIGS = SITHelper.get_configs('troposphere')
    
    def __init__(self):
        self.validate_configs()
        from sit_template import SITTemplate
        self.sit_template = SITTemplate()
        self.template = self.sit_template.template
        self.template_json = self.template.to_json()
        self.cf_helper = CFHelper()
        self.stack_name = self.TROPOSPHERE_CONFIGS['stack_name']
        self.tag_value = self.TROPOSPHERE_CONFIGS['tag_value']

    def validate_configs(self):
        logging.info('Checking configs: troposphere.yml')
        missing_configs = [config for config, value in self.TROPOSPHERE_CONFIGS.iteritems() if value is None]
        if missing_configs:
            Log.error('The following configs have not been added in configs/troposphere.yml: {0}'.format(missing_configs))

    def validate_aws_resources(self):
        #TODO some checks to perform: does AMI exist, does security-group exist, does subnet exist
        pass 

    def validate_template(self):
        self.cf_helper.validate_template(self.template_json)

    def check_if_stack_exists(self):
        if self.cf_helper.stack_exists(self.stack_name):
            Log.error('Your stack already exists!')

    def create_stack(self):
        self.cf_helper.create_stack(self.TROPOSPHERE_CONFIGS['stack_name'], self.template_json, self.tag_value)

    def stack_created_successfully(self):
        if not self.cf_helper.stack_was_created_successfully(self.stack_name):
            Log.error('stack was not created')


def main():
    loader = SITLoader()
    loader.validate_template()
    loader.check_if_stack_exists()
    loader.create_stack()
    loader.stack_created_successfully()

if __name__ == '__main__':
    Log.setup()
    start = time.time()
    main()
    end = time.time()
    logging.info('Your stack is up and ready to go!')
    logging.info('Elapsed time: {0} seconds'.format(end - start))
