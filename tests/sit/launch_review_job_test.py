import sys
import unittest
from boto3.session import Session
from mock import patch
from nose.tools import raises
from fakeredis import FakeRedis
import placebo

from sit.launch_review_job import ReviewJob
from sit.redis_client import RedisClient


class LaunchReviewJobTest(unittest.TestCase):

    def setUp(self):
        self.session = Session(region_name='us-west-1')
        pill = placebo.attach(self.session, 'tests/sit/test_data')
        pill.playback()
        redis_client = FakeRedis()
        jid = 123456
        redis_client.lpush('test-1-php:state.highstate', jid)
        redis_client.lpush('test-1-lb:state.highstate', jid)
        redis_client.set('test-1-php:{0}'.format(jid), '{"result": "false","return": {"test": "true"}}')
        redis_client.set('test-1-lb:{0}'.format(jid), '{"result": "false","return": {"test": "true"}}')
        self.redis_client = RedisClient()
        self.redis_client.redis_instance = redis_client

    @patch.object(ReviewJob, 'check_sit', return_value=None)
    @patch.object(ReviewJob, 'get_cluster', return_value='test-cluster')
    @patch.object(ReviewJob, 'get_autoscaling_group', return_value='test-asg')
    @patch('sit.launch_review_job.RedisClient')
    def test_success(self, *args):
        args[0].return_value = self.redis_client
        launch_review = ReviewJob('test', '1', '1.2.3.4', configs_directory='tests/sit/configs', session=self.session)
        launch_review.CONTAINER_INSTANCE_WAIT = 1
        launch_review.TASK_COMPLETION_WAIT = 1
        launch_review.CLUSTER_RESOURCE_WAIT = 1
        launch_review.run()
        launch_review.check_and_print_results()

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
