import os
import random
import time
import numpy as np
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import sys

sys.path.insert(0, "/storage/src")
from mongo_storage import MongoStorage

sys.path.insert(0, "/cache-service/src")
from cache_manager import RedisCache


mongo = MongoStorage()
redis = RedisCache()

#redis.limpiar_cache() Activar para borrar el cache

# Parámetros del generador
TOTAL_CONSULTAS = 500
DISTRIBUCION = "uniforme"


def generar_intervalos_uniforme(total_consultas, intervalo_min, intervalo_max):
    return np.random.uniform(intervalo_min, intervalo_max, total_consultas)

def generar_intervalos_exponencial(total_consultas, media_intervalo):
    return np.random.exponential(media_intervalo, total_consultas)


def generar_trafico():
    if DISTRIBUCION == "uniforme":
        intervalos = generar_intervalos_uniforme(TOTAL_CONSULTAS, 0.1, 1)
    elif DISTRIBUCION == "exponencial":
        intervalos = generar_intervalos_exponencial(TOTAL_CONSULTAS, 1.0)
    else:
        raise ValueError("Distribución no soportada")

    for i, intervalo in enumerate(intervalos):
        evento = mongo.obtener_evento_aleatorio()
        if evento:
            redis.enviar_evento_a_cache(evento)
        else:
            print(f"❌ No se pudo obtener evento en consulta {i+1}")
        time.sleep(intervalo)

if __name__ == "__main__":
    print(f"🚀 Iniciando generador de tráfico usando distribución: {DISTRIBUCION}")
    generar_trafico()
