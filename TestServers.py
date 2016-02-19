import yaml

class TestServers(object):

    @classmethod
    def get_roles(_self, server):
        roles = _self.init_roles()
        try:
            return roles[server]
        except Exception as e: 
            return 'Failed to find role: {0}. error: {1}'.format(server, e)

    @classmethod
    def get_server_names(_self):
        roles = _self.init_roles()
        return [role_name for role_name, role_list in roles.iteritems()]

    @classmethod
    def init_roles(_self):
        config = _self.get_configs()
        with open(config['roles_path'], 'r') as roles:
            return yaml.load(roles)

    @staticmethod
    def get_configs():
        with open('config.yml', 'r') as configs:
            return yaml.load(configs)
