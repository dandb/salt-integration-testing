import os
import unittest
import placebo
from boto3.session import Session

from helpers.cf_helper import CFHelper
from infrastructure.sit_template import SITTemplate


class CFHelperTest(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_dir = '{0}/test_data'.format(current_dir)
        pill = placebo.attach(self.session, test_dir)
        pill.playback()
        self.cf_helper_placebo = CFHelper(self.session)

    def test_validate_template(self):
        template_body = SITTemplate(self.session).print_template()
        positive_result = self.cf_helper_placebo.validate_template(template_body)
        self.assertEquals(isinstance(positive_result, dict), True)
