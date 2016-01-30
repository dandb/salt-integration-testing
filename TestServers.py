import yaml

class TestServers(object):

    @staticmethod
    def get_roles(server):
        roles = TestServers.init_roles()
        try:
            return roles[server]
        except Exception as e: 
            return 'Failed to find role: {0}. error: {1}'.format(server, e)

    @staticmethod
    def get_server_names():
        roles = TestServers.init_roles()
        return [role_name for role_name, role_list in roles.iteritems()]

    @staticmethod
    def init_roles():
        with open('/opt/ecs_review_job/roles.yml', 'r') as roles:
            return yaml.load(roles)
