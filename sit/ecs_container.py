from helpers.sit_helper import SITHelper


class Container(object):

    def __init__(self, configs_directory=None, family=None, role=None, master_ip=None, env='local'):
        self.sit_helper = SITHelper(configs_directory)
        sit_configs = self.sit_helper.get_configs('sit')
        self.MEMORY = sit_configs['container_memory']
        self.CPU = sit_configs['container_cpu']
        self.IMAGE = sit_configs['container_image']
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
        return ','.join(self.sit_helper.get_states_for_role(role))
