import unittest
from mock import MagicMock
import redis
from fakeredis import FakeRedis

from sit.redis_client import RedisClient


class RedisTest(unittest.TestCase):

    def setUp(self):
        self.redis_client = RedisClient()

    def setup_fakeredis(self):
        redis_client = FakeRedis()
        jid = 123456
        redis_client.lpush('php:state.highstate', jid)
        redis_client.set('php:{0}'.format(jid), '{"result": false}')
        self.redis_client.redis_instance = redis_client

    def test_redis_client_exception(self):
        redis.Redis = MagicMock(side_effect=Exception('boom!'))
        self.redis_client.connect_redis()

    def test_get_highstate_result(self):
        self.setup_fakeredis()
        result = self.redis_client.get_highstate_result('php')
        self.assertEquals(result, '{"result": false}')

    def test_get_highstate_result_failse(self):
        self.redis_client.redis_instance.lindex = MagicMock(side_effect=Exception('boom!'))
        self.redis_client.get_highstate_result('fake-name')
