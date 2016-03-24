#!/usr/bin/env python

import yaml


class SITHelper(object):

    @classmethod
    def get_states_for_role(cls, role):
        roles = cls.get_configs('roles') 
        try:
            return roles[role]
        except Exception as e: 
            return 'Failed to find state list for role: {0}. error: {1}'.format(role, e)

    @classmethod
    def get_roles(cls):
        roles = cls.get_configs('roles') 
        if roles is not None:
            return roles.keys() 
        return False

    @staticmethod
    def get_configs(config_file):
        with open('configs/{0}.yml'.format(config_file), 'r') as configs:
            return yaml.load(configs)
