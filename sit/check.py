import os
import sys
import logging
import yaml
from helpers.sit_helper import SITHelper
from helpers.log import Log
from helpers.cf_helper import CFHelper


class CheckSIT(object):

    ROLES = SITHelper.get_roles()
    SIT_CONFIGS = SITHelper.get_configs('sit')
    TROPOSPHERE_CONFIGS = SITHelper.get_configs('troposphere')

    def __init__(self):
        self.check_configs_are_set()
        self.check_servers_list()
        self.check_roles()
        self.check_stack()

    def check_configs_are_set(self):
        missing_configs = [config for config in self.SIT_CONFIGS if config is None]
        if missing_configs:
            self.log_error('The following configs are not set: {0}'.format(missing_configs))

    def check_servers_list(self):
        if self.ROLES < 1:  
            self.log_error('roles.yml file is not setup properly. You require at least one role to test')

    def check_roles(self):
        roles_with_no_states = [role for role in self.ROLES if not SITHelper.get_states_for_roles(role)]
        if roles_with_no_states:
            self.log_error('The following servers are missing roles inside of roles.yml file: {0}'.format(servers_with_no_roles))

    def check_stack(self):
        cf_helper = CFHelper()  
        stack_name = self.TROPOSPHERE_CONFIGS['stack_name']
        if not cf_helper.get_stack_info(stack_name, 15):
            self.log_error('Stack "{0}" does not exist. Please run setup_troposphere'.format(stack_name))
            
    def log_error(self, message, e=None):
        logging.error('Message: {0}. Error: {1}.'.format(message, e))
        sys.exit(1)

def main():
        Log.setup(logging.ERROR)
        setup_sit = CheckSIT()
        

if __name__ == '__main__':
    main()
