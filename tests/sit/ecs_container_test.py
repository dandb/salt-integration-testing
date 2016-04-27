import unittest
from mock import MagicMock

from sit.ecs_container import Container
from helpers.sit_helper import SITHelper


class UserDataTest(unittest.TestCase):
    
    def setUp(self):
        configs_directory = 'tests/sit/configs'
        self.container = Container(configs_directory)
        self.container.master_ip = '1.2.3.4'
        self.container.env = 'qa'
        self.container.family = 'test'
        self.container.role = 'unit'
        self.container.MEMORY = 10
        self.container.sit_helper = SITHelper(configs_directory)
        self.container.sit_helper.get_states_for_role = MagicMock(return_value=['server', 'php'])

    def test_environment_dictionary(self):
        result = self.container.get_environment_dictionary('test', 'value')
        self.assertEquals(result, {"name": 'test', "value": 'value'})

    def test_get_environment_variables(self):
        result = self.container.get_container_definitions()
        expected_answer = {'environment': [{'name': 'roles', 'value': 'server,php'}, {'name': 'env', 'value': 'qa'}, {'name': 'master', 'value': '1.2.3.4'}, {'name': 'minion_id', 'value': 'test'}], 'image': 'dandb/salt_review:2015-8-7', 'cpu': 512, 'name': 'test', 'memory': 10}
        self.assertEquals(result, expected_answer)
