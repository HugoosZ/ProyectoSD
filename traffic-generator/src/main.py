import os
import random
import time
import numpy as np
import redis
from pymongo import MongoClient
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv(dotenv_path='mongo.env')
load_dotenv(dotenv_path='redis.env')

# Configuración MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "waze_traffic"
COLLECTION_NAME = "events"

# Configuración Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # Nombre del servicio en docker-compose
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Parámetros del generador
TOTAL_CONSULTAS = 500
DISTRIBUCION = "uniforme"

# Conexión a MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Conexión a Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def generar_intervalos_uniforme(total_consultas, intervalo_min, intervalo_max):
    return np.random.uniform(intervalo_min, intervalo_max, total_consultas)

def generar_intervalos_exponencial(total_consultas, media_intervalo):
    return np.random.exponential(media_intervalo, total_consultas)

def obtener_evento_aleatorio():
    total_documentos = collection.estimated_document_count()
    if total_documentos == 0:
        print("⚠️ No hay eventos almacenados")
        return None

    indice_aleatorio = random.randint(0, total_documentos - 1)
    evento = collection.find().skip(indice_aleatorio).limit(1)
    for doc in evento:
        return doc
    return None

def enviar_evento_a_cache(evento):
    """Envía el evento al cache Redis"""
    if not evento:
        return

    evento.pop('_id', None)  # 👈 Elimina el campo '_id' si existe
    clave = f"{evento.get('tipo')}_{evento.get('lat')}_{evento.get('lon')}_{evento.get('subtipo')}"
    valor = json.dumps(evento)

    r.set(clave, valor, ex=600)
    print(f"📥 Evento enviado al cache: {clave}")

def generar_trafico():
    if DISTRIBUCION == "uniforme":
        intervalos = generar_intervalos_uniforme(TOTAL_CONSULTAS, 0.5, 2.0)
    elif DISTRIBUCION == "exponencial":
        intervalos = generar_intervalos_exponencial(TOTAL_CONSULTAS, 1.0)
    else:
        raise ValueError("Distribución no soportada")

    for i, intervalo in enumerate(intervalos):
        evento = obtener_evento_aleatorio()
        if evento:
            enviar_evento_a_cache(evento)
        else:
            print(f"❌ No se pudo obtener evento en consulta {i+1}")
        time.sleep(intervalo)

if __name__ == "__main__":
    print(f"🚀 Iniciando generador de tráfico usando distribución: {DISTRIBUCION}")
    generar_trafico()
