import os
import unittest
from boto3.session import Session
from mock import patch
from nose.tools import raises
import placebo

from sit.launch_review_job import ReviewJob


class LaunchReviewJobTest(unittest.TestCase):

    def setUp(self):
        self.session = Session(region_name='us-west-1')
        pill = placebo.attach(self.session, 'tests/sit/test_data')
        pill.playback()

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    def test_success(self, *args):
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        launch_review.init_instance()
        launch_review.run()
        launch_review.check_and_print_results()

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    @raises(SystemExit)
    def test_wait_for_instance_to_be_active_raises_error(self, *args):
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        self.assertEquals(launch_review.wait_for_instance_to_be_active(31), launch_review.error())

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    @raises(SystemExit)
    def test_get_launched_instance_name_raises_error(self, *args):
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        self.assertEquals(launch_review.get_launched_instance_name(current_instances=None, attempt=30), launch_review.error())

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    def test_highstate_failed(self, *args):
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        results = ['"result": false', 'Data failed to compile:', 'Pillar failed to render with the following messages:']
        for result in results:
            self.assertEquals(launch_review.highstate_failed('foo {0} bar'.format(result)), True)

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    def test_check_regex_failure(self, *args):
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        result = "foo Rendering SLS 'local:apache' failed: bar"
        self.assertEquals(launch_review.highstate_failed(result), True)
        result_false = "foo bar"
        self.assertEquals(launch_review.highstate_failed(result_false), False)
