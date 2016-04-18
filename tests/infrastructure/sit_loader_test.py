import unittest
from mock import MagicMock
from boto3.session import Session

from infrastructure.sit_loader import SITLoader
from infrastructure.sit_template import SITTemplate
from helpers.cf_helper import CFHelper


class SITLoaderTest(unittest.TestCase):

    def setUp(self):
        self.session = Session(region_name='us-west-1')
        configs_directory = 'tests/sit/configs'
        self.sit_loader = SITLoader(session=self.session, configs_directory=configs_directory)
        self.mock_cf_helper_true_responses()

    def mock_cf_helper_true_responses(self):
        cf_helper = CFHelper(self.session)
        cf_helper.get_stack_info = MagicMock(return_value=True)
        cf_helper.validate_template = MagicMock(return_value=True)
        cf_helper.create_stack = MagicMock(return_value=True)
        cf_helper.stack_was_created_successfully = MagicMock(return_value=True)
        self.sit_loader.cf_helper = cf_helper

    def test_successful_run(self):
        self.sit_loader.run()

