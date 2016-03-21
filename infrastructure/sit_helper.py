import yaml


class SITHelper(object):

    @staticmethod
    def get_configs():
        with open('config.yml', 'r') as configs:
            return yaml.load(configs)
