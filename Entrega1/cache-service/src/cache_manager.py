import redis
import os
from typing import Optional
import json
from pymongo import MongoClient
from bson import ObjectId  


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
    
    def enviar_evento_a_cache(self,evento):
        """Envía el evento al cache Redis"""
        if not evento:
            return

        
        # clave = f"{evento.get('ciudad')}_{evento.get('tipo')}" si quiero usar como llave algo que no sea id basta con esto 

        if "_id" in evento and isinstance(evento["_id"], ObjectId):
            evento["_id"] = str(evento["_id"])

        clave = evento["_id"]
        valor = json.dumps(evento)

        valor_existente = self.client.get(clave)
        if valor_existente:
            print(f"🔁🔁🔁🔁🔁 La clave '{clave}' ya existía en cache. Será actualizada.")
            print(f"📤 Valor anterior: {valor_existente}")
        else:
            print(f"🆕 La clave '{clave}' no existía. Será insertada.")

        self.client.set(clave, valor)
        

    def limpiar_cache(self):
        """Elimina todas las claves del Redis actual (flush de la base de datos)."""
        self.client.flushdb()
        print("🧹 Cache de Redis limpiado completamente.")