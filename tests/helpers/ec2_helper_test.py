import os
import unittest
import placebo
from boto3.session import Session

from helpers.ec2_helper import EC2Helper


class EC2HelperTest(unittest.TestCase):
    
    def setUp(self):
        self.ec2_helper = EC2Helper()
        session = Session()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_dir = '{0}/test_data'.format(current_dir)
        pill = placebo.attach(session, test_dir)
        pill.playback()
        self.ec2_helper_placebo = EC2Helper(session)

    def test_describe_key_pairs(self):
        positive_result = self.ec2_helper_placebo.describe_key_pairs(['SEB'])
        self.assertEquals(isinstance(positive_result, dict), True)
        negative_result = self.ec2_helper_placebo.describe_key_pairs(['SB'])
        self.assertEquals(isinstance(negative_result, dict), False)
        self.assertFalse(negative_result)

    def test_describe_images(self):
        positive_result = self.ec2_helper_placebo.describe_images(['ami-33679c75'])
        self.assertEquals(isinstance(positive_result, dict), True)
        negative_result = self.ec2_helper_placebo.describe_images(['ami-fake'])
        self.assertEquals(isinstance(negative_result, dict), False)
        self.assertFalse(negative_result)

    def test_describe_security_groups(self):
        positive_result = self.ec2_helper_placebo.describe_security_groups(['sg-123456'])
        self.assertEquals(isinstance(positive_result, dict), True)
        negative_result = self.ec2_helper_placebo.describe_security_groups(['sg-fake'])
        self.assertEquals(isinstance(negative_result, dict), False)
        self.assertFalse(negative_result)

    def test_describe_subnets_exception(self):
        positive_result = self.ec2_helper_placebo.describe_subnets(['subnet-123456'])
        self.assertEquals(isinstance(positive_result, dict), True)
        negative_result = self.ec2_helper_placebo.describe_subnets(['subnet-fake'])
        self.assertEquals(isinstance(negative_result, dict), False)
        self.assertFalse(negative_result)

