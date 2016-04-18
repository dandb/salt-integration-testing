import unittest

from infrastructure.sit_template import SITTemplate


class SIT(unittest.TestCase):
    
    def setUp(self):
        configs_directory = 'tests/sit/configs'
        self.sit_template = SITTemplate(configs_directory)

    def test_print_template(self):
        result = self.sit_template.print_template()
        self.assertEquals(result, None)


