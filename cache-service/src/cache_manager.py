import redis
import os
from typing import Optional

class RedisCache:
    def __init__(self):
        print("✅ Redis inicializado correctamente.")  
        policy = os.getenv("REDIS_HOST", "uniform-lru")
        host_map = {
            "uniform-lru": "redis-uniform-lru",
            "uniform-lfu": "redis-uniform-lfu",
            "exp-lru": "redis-exp-lru",
            "exp-lfu": "redis-exp-lfu"
        }

        redis_host = host_map.get(policy)
        redis_port = int(os.getenv("REDIS_PORT", 6379))

        print(f"✅ Conectando a Redis: {redis_host}:{redis_port}")

        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self._test_connection()

    def _test_connection(self):
        """Verifica que Redis esté accesible."""
        try:
            self.client.ping()
        except redis.ConnectionError as e:
            raise RuntimeError(f"Error conectando a Redis: {e}")

    def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Guarda un valor con TTL opcional (segundos)."""
        self.client.set(key, value, ex=ttl)

    def get(self, key: str) -> Optional[str]:
        """Obtiene un valor o None si no existe."""
        return self.client.get(key)