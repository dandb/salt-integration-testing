import os
import unittest
from boto3.session import Session
from mock import patch
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

