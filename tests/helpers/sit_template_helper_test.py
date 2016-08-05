import unittest
from mock import MagicMock
from nose.tools import raises
from boto3.session import Session

from helpers.sit_template_helper import SITTemplateHelper


class SitHelperTest(unittest.TestCase):

    def setUp(self):
        self.sit_template_helper = self.get_sit_template_helper()
        self.sit_template_helper.open_url = MagicMock(return_value=None)
        self.set_ec2_helper_mocks_true()

    def get_sit_template_helper(self, configs_directory='configs'):
        session = Session(region_name='us-west-1')
        return SITTemplateHelper(session=session, configs_directory='tests/helpers/{0}'.format(configs_directory))

    def set_ec2_helper_mocks_true(self):
        self.sit_template_helper.ec2_helper.describe_key_pairs = MagicMock(return_value=True)
        self.sit_template_helper.ec2_helper.describe_images = MagicMock(return_value=True)
        self.sit_template_helper.ec2_helper.describe_security_groups = MagicMock(return_value=True)
        self.sit_template_helper.ec2_helper.describe_subnets = MagicMock(return_value=True)

    def test_successful_validate(self):
        self.sit_template_helper.validate()

    @raises(SystemExit)
    def test_validate_configs(self):
        sit_template_helper = self.get_sit_template_helper('empty_configs')
        self.assertRaises(sit_template_helper.validate_configs(), Exception)

    @raises(SystemExit)
    def test_validate_aws_resources_false_key_pair(self):
        self.sit_template_helper.ec2_helper.describe_key_pairs = MagicMock(return_value=False)
        self.assertRaises(self.sit_template_helper.validate_aws_resources(), Exception)

    @raises(SystemExit)
    def test_validate_aws_resources_false_describe_images(self):
        self.sit_template_helper.ec2_helper.describe_images = MagicMock(return_value=False)
        self.assertRaises(self.sit_template_helper.validate_aws_resources(), Exception)

    @raises(SystemExit)
    def test_validate_aws_resources_false_security_groups(self):
        self.sit_template_helper.ec2_helper.describe_security_groups = MagicMock(return_value=False)
        self.assertRaises(self.sit_template_helper.validate_aws_resources(), Exception)

    @raises(SystemExit)
    def test_validate_aws_resources_false_describe_subnets(self):
        self.sit_template_helper.ec2_helper.describe_subnets = MagicMock(return_value=False)
        self.assertRaises(self.sit_template_helper.validate_aws_resources(), Exception)
