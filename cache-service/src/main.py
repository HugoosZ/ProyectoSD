# from src.removal_policies.lru import LRUCache
# from src.removal_policies.lfu import LFUCache

import hashlib
import time

from cache_manager import RedisCache

cache = RedisCache()

cache.set("hola", "mundo")
print("✅ Valor desde Redis:", cache.get("hola"))

while True:
    print("✅ Redis inicializado correctamente.")
    time.sleep(5)  # Evita saturar la CPU
