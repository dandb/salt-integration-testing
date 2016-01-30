import redis
import logging


class RedisClient(object):
    """
    Redis Pillar for retrieving and saving VPN data for AWS accounts' regions.
    """

    HIGHSTATE = 'state.highstate'

    logging.basicConfig(level=logging.INFO)

    def __init__(self):
        self.redis_instance = self.connect_redis()

    def connect_redis(self,  host='localhost', port=6379, timeout=2):
        try:
            return redis.Redis(host=host, port=port, socket_timeout=timeout)
        except:
            self.log.warning("cannot connect to redis")

    def get_highstate_result(self, family):
        try:
            jid = self.redis_instance.lindex('{0}:{1}'.format(family, self.HIGHSTATE), 0)
            return self.redis_instance.get('{0}:{1}'.format(family, jid))
        except Exception as e:
            self.log.error('Failed to get highstate results: {0}'.format(e))
