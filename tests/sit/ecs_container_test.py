import unittest

from sit.ecs_container import Container


class UserDataTest(unittest.TestCase):
    
    def setUp(self):
        self.container = Container()
        self.container.master_ip = '1.2.3.4'
        self.container.env = 'qa'
        self.container.family = 'test'
        self.container.role = 'unit'
        self.container.MEMORY = 10

    def test_environment_dictionary(self):
        result = self.container.get_environment_dictionary('test', 'value')
        self.assertEquals(result, {"name": 'test', "value": 'value'})
