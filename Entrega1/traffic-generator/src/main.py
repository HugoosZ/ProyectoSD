import os
import random
import time
import numpy as np
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import sys
import matplotlib.pyplot as plt
from signal import signal, SIGINT

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


# Variables para métricas
hits = 0
misses = 0
hitrate_evolucion = []
consulta_n = []
consulta_actual = 0

def generar_grafico():
    plt.figure(figsize=(10, 5))
    plt.plot(consulta_n, hitrate_evolucion, label="Hitrate (%)", color='blue')
    plt.xlabel("Número de consultas")
    plt.ylabel("Hitrate (%)")
    plt.title("Evolución del Hitrate")
    plt.ylim(0, 100)
    plt.grid(True)
    plt.legend()
    plt.savefig("hitrate_grafico.png")
    plt.show()
    print("📊 Gráfico guardado como 'hitrate_grafico.png'")

def handler(sig, frame):
    print("\n🛑 Interrupción detectada (Ctrl+C)")
    generar_grafico()
    exit(0)

signal(SIGINT, handler)  # Captura Ctrl+C

def generar_trafico():
    global hits, misses, consulta_actual

    if DISTRIBUCION == "uniforme":
        intervalos = generar_intervalos_uniforme(TOTAL_CONSULTAS, 0.5, 2.0)
    elif DISTRIBUCION == "exponencial":
        intervalos = generar_intervalos_exponencial(TOTAL_CONSULTAS, 1.0)
    else:
        raise ValueError("Distribución no soportada")

    for intervalo in intervalos:
        consulta_actual += 1
        evento = mongo.obtener_evento_aleatorio()
        
        if evento:
            # Suponiendo que RedisCache tenga un método para verificar si ya está en caché:
            evento_id = evento.get("_id")
            if redis.existe_en_cache(evento_id):
                hits += 1
            else:
                misses += 1
                redis.enviar_evento_a_cache(evento)

            total = hits + misses
            hitrate = (hits / total) * 100
            hitrate_evolucion.append(hitrate)
            consulta_n.append(consulta_actual)

        else:
            print(f"❌ No se pudo obtener evento en consulta {consulta_actual}")
        
        time.sleep(intervalo)

    print(f"\n✅ Hitrate final: {hitrate:.2f}% ({hits} hits de {total} consultas)")
    generar_grafico()

if __name__ == "__main__":
    print(f"🚀 Iniciando generador de tráfico usando distribución: {DISTRIBUCION}")
    generar_trafico()
