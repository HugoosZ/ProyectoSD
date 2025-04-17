import redis
import os

class RedisCache:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            username=os.getenv("REDIS_USER"),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )

    def set(self, key, value):
        self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)