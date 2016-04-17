import unittest
from mock import MagicMock

from infrastructure.sit_loader import SITLoader
from infrastructure.sit_template import SITTemplate
from helpers.cf_helper import CFHelper


class SITLoaderTest(unittest.TestCase):
    
    def setUp(self):
        configs_directory = 'tests/sit/configs'
        self.sit_loader = SITLoader(configs_directory)
        self.cf_helper = CFHelper()
        self.cf_helper.get_stack_info = MagicMock(return_value=True)
        self.sit_template = SITTemplate(configs_directory)

