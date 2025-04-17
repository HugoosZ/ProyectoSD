import redis
import json

class RedisCache:
    def __init__(self, host="redis", port=6379, ttl=600):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        self.ttl = ttl

    def set(self, key, value):
        self.client.set(key, json.dumps(value), ex=self.ttl)

    def get(self, key):
        data = self.client.get(key)
        return json.loads(data) if data else None

    def exists(self, key):
        return self.client.exists(key)

    def clear(self):
        self.client.flushdb()