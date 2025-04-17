import redis
import os
from typing import Optional

class RedisCache:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),  # Default para Docker
            port=int(os.getenv("REDIS_PORT", 6379)),
            username=os.getenv("REDIS_USER", ""),   # Default vacío
            password=os.getenv("REDIS_PASSWORD", ""),
            decode_responses=True,
            socket_connect_timeout=5  # Timeout para conexión
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