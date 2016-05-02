#!/usr/bin/env python

import yaml


class SITHelper(object):

    def __init__(self, configs_directory=None):
        self.configs_directory = configs_directory

    def get_states_for_role(self, role):
        roles = self.get_configs('roles')
        try:
            return roles[role]
        except Exception as e: 
            return 'Failed to find state list for role: {0}. error: {1}'.format(role, e)

    def get_roles(self):
        roles = self.get_configs('roles')
        if roles is not None:
            return roles.keys() 
        return False

    def get_configs(self, config_file):
        with open('{0}/{1}.yml'.format(self.configs_directory, config_file), 'r') as configs:
            return yaml.load(configs)

    def get_custom_user_data(self):
        with open('{0}/custom_user_data.sh'.format(self.configs_directory), 'r') as custom_user_data:
            return custom_user_data.read()
