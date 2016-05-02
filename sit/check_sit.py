#!/usr/bin/env python

from helpers.sit_helper import SITHelper
from helpers.cf_helper import CFHelper
from helpers.log import Log


class CheckSIT(object):

    def __init__(self, configs_directory=None, session=None):
        self.sit_helper = SITHelper(configs_directory)
        self.ROLES = self.sit_helper.get_roles()
        self.SIT_CONFIGS = self.sit_helper.get_configs('sit')
        self.TROPOSPHERE_CONFIGS = self.sit_helper.get_configs('troposphere')
        self.cf_helper = CFHelper(configs_directory=configs_directory, session=session)

    def check_configs_are_set(self):
        missing_configs = [config for config, value in self.SIT_CONFIGS.iteritems() if value is None]
        if missing_configs:
            Log.error('The following configs are not set: {0}'.format(missing_configs))

    def check_roles_file(self):
        if self.ROLES < 1:  
            Log.error('roles.yml file is not setup properly. You require at least one role to test')

    def check_roles_not_empty(self):
        empty_roles = [role for role in self.ROLES if not self.sit_helper.get_states_for_role(role)]
        if empty_roles:
            Log.error('The following servers are missing roles inside of roles.yml file: {0}'.format(empty_roles))

    def check_stack_exists(self):
        stack_name = self.TROPOSPHERE_CONFIGS['stack_name']
        if not self.cf_helper.get_stack_info(stack_name):
            Log.error('Stack "{0}" does not exist. Please run setup_troposphere'.format(stack_name))
            
    def run(self):
        self.check_configs_are_set()
        self.check_roles_file()
        self.check_roles_not_empty()
        self.check_stack_exists()

if __name__ == '__main__':
    Log.setup()
    CheckSIT().run()
