from helpers.sit_helper import SITHelper


class Container(object):

    SIT_HELPER = SITHelper()
    CONFIGS = SIT_HELPER.get_configs('sit')
    MEMORY = CONFIGS['container_memory']
    CPU = CONFIGS['container_cpu']
    IMAGE = CONFIGS['container_image']

    def __init__(self, family=None, role=None, master_ip=None, env='local'):
        self.family = family
        self.role = role
        self.master_ip = master_ip
        self.env = env

    def get_container_definitions(self):
        return {
            "name": self.family,
            "memory": self.MEMORY,
            "cpu": self.CPU,
            "image": self.IMAGE,
            "environment": self.get_environment_variables()
        }

    def get_environment_variables(self):
        environment_variables = list()
        environment_variables.append(Container.get_environment_dictionary('roles', self.get_role_states(self.role)))
        environment_variables.append(Container.get_environment_dictionary('env', self.env))
        environment_variables.append(Container.get_environment_dictionary('master', self.master_ip))
        environment_variables.append(Container.get_environment_dictionary('minion_id', self.family))
        return environment_variables

    @staticmethod
    def get_environment_dictionary(name, value):
        return {"name": name, "value": value}

    def get_role_states(self, role):
        return ','.join(self.SIT_HELPER.get_states_for_role(role))
