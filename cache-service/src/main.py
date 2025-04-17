# from src.removal_policies.lru import LRUCache
# from src.removal_policies.lfu import LFUCache

import hashlib
import time

from cache_manager import RedisCache

cache = RedisCache()

cache.set("hola", "mundo")
print("✅ Valor desde Redis:", cache.get("hola"))

# # Modo: usar redis o modo local
# USE_REDIS = True

# if USE_REDIS:
#     cache = RedisCache(ttl=600)
# else:
#     cache = LRUCache(capacity=100)

# def generar_clave(evento):
#     raw = f"{evento['tipo']}_{evento['lat']}_{evento['lon']}_{evento['subtipo']}"
#     return hashlib.md5(raw.encode()).hexdigest()

# def registrar_eventos(lista_eventos):
#     for evento in lista_eventos:
#         clave = generar_clave(evento)
#         if cache.get(clave):
#             print("⚠️ Ya estaba en cache:", evento["ubicacion"])
#         else:
#             cache.set(clave, evento)
#             print("✅ Evento nuevo:", evento["ubicacion"])

# # Simulación
# if __name__ == "__main__":
#     evento_simulado = {
#         "tipo": "accidente",
#         "subtipo": "leve",
#         "ubicacion": "Av. Apoquindo",
#         "lat": -33.417,
#         "lon": -70.607,
#         "hora": time.time()
#     }

#     registrar_eventos([evento_simulado])