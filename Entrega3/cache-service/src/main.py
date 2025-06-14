import hashlib
import time

from cache_manager import RedisCache

cache = RedisCache()

while True:
    time.sleep(5)  
