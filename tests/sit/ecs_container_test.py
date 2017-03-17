import unittest
from mock import MagicMock

from sit.ecs_container import Container
from helpers.sit_helper import SITHelper


class UserDataTest(unittest.TestCase):
    
    def setUp(self):
        self.configs_directory = 'tests/sit/configs'
        self.container = self.create_container()

    def create_container(self, redis_host=None):
        container = Container(configs_directory=self.configs_directory,
                              redis_host=redis_host, master_ip='1.2.3.4', env='qa', family='test', role='unit')
        container.MEMORY = 10
        container.sit_helper.get_states_for_role = MagicMock(return_value=['server', 'php'])
        return container

    def test_environment_dictionary(self):
        result = self.container.get_environment_dictionary('test', 'value')
        self.assertEquals(result, {"name": 'test', "value": 'value'})

    def test_get_environment_variables(self):
        result = self.container.get_container_definitions()
        expected_answer = {'memoryReservation': 256, 'name': 'test', 'image': 'dandb/salt_review:2015-8-7', 'environment': [{'name': 'roles', 'value': 'server,php'}, {'name': 'env', 'value': 'qa'}, {'name': 'master', 'value': '1.2.3.4'}, {'name': 'minion_id', 'value': 'test'}, {'name': 'redis_host', 'value': '1.2.3.4'}], 'memory': 10, 'cpu': 512}
        self.assertEquals(result, expected_answer)

    def test_get_environment_varuables_with_redis_hist(self):
        container = self.create_container(redis_host='localhost')
        result = container.get_container_definitions()
        expected_answer = {'memoryReservation': 256, 'name': 'test', 'image': 'dandb/salt_review:2015-8-7', 'environment': [{'name': 'roles', 'value': 'server,php'}, {'name': 'env', 'value': 'qa'}, {'name': 'master', 'value': '1.2.3.4'}, {'name': 'minion_id', 'value': 'test'}, {'name': 'redis_host', 'value': 'localhost'}], 'memory': 10, 'cpu': 512}
        self.assertEquals(result, expected_answer)
