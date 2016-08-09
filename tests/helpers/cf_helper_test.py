import os
import unittest
import placebo
from nose.tools import raises
from boto3.session import Session

from helpers.cf_helper import CFHelper
from infrastructure.sit_loader import SITLoader
from infrastructure.sit_template import SITTemplate


class CFHelperTest(unittest.TestCase):

    def setUp(self):
        session = Session(region_name='us-west-1')
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_dir = '{0}/test_data'.format(current_dir)
        pill = placebo.attach(session, test_dir)
        pill.playback()

        self.configs_directory = 'tests/sit/configs'
        self.cf_helper_placebo = CFHelper(configs_directory=self.configs_directory, session=session)
        self.sit_loader_placebo = SITLoader(configs_directory=self.configs_directory, session=session)

    @raises(SystemExit)
    def test_validate_template(self):
        template_body = SITTemplate(self.configs_directory).template.to_json()
        negative_result = self.cf_helper_placebo.validate_template(template_body)
        self.assertEquals(negative_result, None)

    def test_create_stack_success(self):
        positive_result = self.cf_helper_placebo.create_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)
        self.assertEquals(positive_result, None)

    def test_update_stack_success(self):
        positive_result = self.cf_helper_placebo.update_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)
        self.assertEquals(positive_result, None)

    @raises(SystemExit)
    def test_create_stack_failure(self):
        positive_result = self.cf_helper_placebo.create_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)
        self.assertEquals(positive_result, None)
        self.cf_helper_placebo.create_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)

    @raises(SystemExit)
    def test_update_stack_failure(self):
        positive_result = self.cf_helper_placebo.update_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)
        self.assertEquals(positive_result, None)
        self.cf_helper_placebo.update_stack(self.sit_loader_placebo.STACK_NAME, self.sit_loader_placebo.template_json, self.sit_loader_placebo.TAG_VALUE)

    def test_stack_was_created_successfully(self):
        attempts = 25  # set attempts to the max so that it only tries once
        positive_result = self.cf_helper_placebo.stack_was_created_successfully(self.sit_loader_placebo.STACK_NAME, attempts, 0)
        self.assertEquals(positive_result, True)

        # failed status
        negative_result = self.cf_helper_placebo.stack_was_created_successfully(self.sit_loader_placebo.STACK_NAME, attempts, 0)
        self.assertEquals(negative_result, False)

        # too many attempts
        negative_result = self.cf_helper_placebo.stack_was_created_successfully(self.sit_loader_placebo.STACK_NAME, attempts + 1, 0)
        self.assertEquals(negative_result, False)

        # bad status
        negative_result = self.cf_helper_placebo.stack_was_created_successfully(self.sit_loader_placebo.STACK_NAME, attempts, 0)
        self.assertEquals(negative_result, False)

    @raises(SystemExit)
    def test_get_resource_name(self):
        # this call will raise the SystemExit because the stack has already been created
        self.cf_helper_placebo.get_resource_name(self.sit_loader_placebo.STACK_NAME, 'AutoFailingGroup')
