#!/usr/bin/env python

from helpers.sit_helper import SITHelper
from helpers.cf_helper import CFHelper
from helpers.log import Log


class CheckSIT(object):

    ROLES = SITHelper.get_roles()
    SIT_CONFIGS = SITHelper.get_configs('sit')
    TROPOSPHERE_CONFIGS = SITHelper.get_configs('troposphere')

    def __init__(self):
        self.cf_helper = CFHelper()

    def check_configs_are_set(self):
        missing_configs = [config for config in self.SIT_CONFIGS if config is None]
        if missing_configs:
            Log.error('The following configs are not set: {0}'.format(missing_configs))

    def check_roles_file(self):
        if self.ROLES < 1:  
            Log.error('roles.yml file is not setup properly. You require at least one role to test')

    def check_roles_not_empty(self):
        empty_roles = [role for role in self.ROLES if not SITHelper.get_states_for_role(role)]
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
