import unittest
from nose.tools import raises
from boto3.session import Session

from sit.check_sit import CheckSIT
from helpers.sit_helper import SITHelper
from mock import MagicMock


class CheckSITTest(unittest.TestCase):

    def setUp(self):
        session = Session(region_name='us-west-1')
        self.check_sit = CheckSIT(configs_directory='tests/sit/configs', session=session)

    def set_values(self, configs_location):
        self.check_sit.SIT_HELPER = SITHelper(configs_directory=configs_location)
        self.check_sit.ROLES = self.check_sit.SIT_HELPER.get_roles()
        self.check_sit.SIT_CONFIGS = self.check_sit.SIT_HELPER.get_configs('sit')
        self.check_sit.TROPOSPHERE_CONFIGS = self.check_sit.SIT_HELPER.get_configs('troposphere')

    def mock_cf_response(self, response=True):
        self.check_sit.cf_helper.get_stack_info = MagicMock(return_value=response)

    def test_run_successfully(self):
        self.set_values('tests/sit/configs')
        self.mock_cf_response()
        self.check_sit.run()

    @raises(SystemExit)
    def test_check_stack_exists_raises_error(self):
        self.set_values('tests/sit/missing_configs')
        self.mock_cf_response(response=False)
        self.assertRaises(self.check_sit.check_stack_exists(), Exception)

    @raises(SystemExit)
    def test_configs_are_set(self):
        self.set_values('tests/sit/missing_configs')
        self.assertRaises(self.check_sit.check_configs_are_set(), Exception)

    @raises(SystemExit)
    def test_check_roles_not_empty(self):
        self.set_values('tests/sit/missing_configs')
        self.assertRaises(self.check_sit.check_roles_not_empty(), Exception)

    @raises(SystemExit)
    def test_check_roles(self):
        self.set_values('tests/sit/missing_role')
        self.assertRaises(self.check_sit.check_roles_file(), Exception)
