import unittest
from mock import MagicMock
from boto3.session import Session
from nose.tools import raises

from infrastructure.sit_loader import SITLoader
from helpers.cf_helper import CFHelper


class SITLoaderTest(unittest.TestCase):

    def setUp(self):
        self.session = Session(region_name='us-west-1')
        self.configs_directory = 'tests/sit/configs'
        self.sit_loader = SITLoader(session=self.session, configs_directory=self.configs_directory)
        self.mock_cf_helper_true_responses()

    def mock_cf_helper_true_responses(self):
        cf_helper = CFHelper(configs_directory=self.configs_directory, session=self.session)
        cf_helper.get_stack_info = MagicMock(return_value=True)
        cf_helper.validate_template = MagicMock(return_value=True)
        cf_helper.create_stack = MagicMock(return_value=True)
        cf_helper.stack_was_created_successfully = MagicMock(return_value=True)
        self.sit_loader.cf_helper = cf_helper

    def test_successful_run(self):
        self.sit_loader.run()

    @raises(SystemExit)
    def test_failed_run(self):
        self.sit_loader.cf_helper.stack_was_created_successfully = MagicMock(return_value=False)
        self.assertRaises(self.sit_loader.stack_created_successfully(), Exception)

