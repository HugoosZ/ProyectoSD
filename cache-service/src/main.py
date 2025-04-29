# from src.removal_policies.lru import LRUCache
# from src.removal_policies.lfu import LFUCache

import hashlib
import time

from cache_manager import RedisCache

cache = RedisCache()

while True:
    time.sleep(5)  # Evita saturar la CPU
