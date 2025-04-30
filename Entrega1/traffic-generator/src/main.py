import os
import random
import time
import numpy as np
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import sys
from signal import signal, SIGINT

sys.path.insert(0, "/storage/src")
from mongo_storage import MongoStorage

sys.path.insert(0, "/cache-service/src")
from cache_manager import RedisCache


mongo = MongoStorage()
redis = RedisCache()

#redis.limpiar_cache() Activar para borrar el cache

# Parámetros del generador

TOTAL_CONSULTAS = 10
DISTRIBUCION = "uniforme"



def generar_trafico():
    stats = {"total": 0, "hits": 0}

    for i in range(TOTAL_CONSULTAS):
        if DISTRIBUCION == "uniforme":
            evento = mongo.obtener_evento_uniforme()
            intervalo = np.random.uniform(0.1, 1.0)

        elif DISTRIBUCION == "exponencial":
            evento = mongo.obtener_evento_exponencial()
            intervalo = np.random.exponential(1.0)

        else:
            raise ValueError("Distribución no soportada")

        if evento:
            redis.enviar_evento_a_cache(evento,stats)
        else:
            print(f"❌ No se pudo obtener evento en consulta {i+1}")
            
    
        time.sleep(intervalo)

    print(f"\n📊 Estadísticas finales:")
    print(f"🔢 Total de consultas: {stats['total']}")
    print(f"✅ Hits (ya estaba en cache): {stats['hits']}")
    print(f"➕ Inserts nuevos: {stats['total'] - stats['hits']}")    

if __name__ == "__main__":
    print(f"🚀 Iniciando generador de tráfico usando distribución: {DISTRIBUCION}")
    generar_trafico()
