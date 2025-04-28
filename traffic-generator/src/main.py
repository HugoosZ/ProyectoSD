import os
import random
import time
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(dotenv_path='mongo.env')

# Configuración MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "waze_traffic"
COLLECTION_NAME = "events"

# Parámetros del generador
TOTAL_CONSULTAS = 500  # Número total de consultas a simular
DISTRIBUCION = os.getenv("TRAFFIC_DISTRIBUTION", "uniforme")  # "uniforme" o "exponencial"

# Configurar conexión
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def generar_intervalos_uniforme(total_consultas, intervalo_min, intervalo_max):
    """Genera intervalos de espera basados en distribución uniforme"""
    return np.random.uniform(intervalo_min, intervalo_max, total_consultas)

def generar_intervalos_exponencial(total_consultas, media_intervalo):
    """Genera intervalos de espera basados en distribución exponencial"""
    return np.random.exponential(media_intervalo, total_consultas)

def obtener_evento_aleatorio():
    """Obtiene un evento aleatorio desde MongoDB"""
    total_documentos = collection.estimated_document_count()
    if total_documentos == 0:
        print("⚠️ No hay eventos almacenados")
        return None

    indice_aleatorio = random.randint(0, total_documentos - 1)
    evento = collection.find().skip(indice_aleatorio).limit(1)
    for doc in evento:
        return doc
    return None

def generar_trafico():
    """Genera tráfico consultando eventos a distintas tasas"""
    if DISTRIBUCION == "uniforme":
        intervalos = generar_intervalos_uniforme(TOTAL_CONSULTAS, 0.5, 2.0)  # en segundos
    elif DISTRIBUCION == "exponencial":
        intervalos = generar_intervalos_exponencial(TOTAL_CONSULTAS, 1.0)  # media = 1 segundo
    else:
        raise ValueError("Distribución no soportada")

    for i, intervalo in enumerate(intervalos):
        evento = obtener_evento_aleatorio()
        if evento:
            print(f"🔎 Consulta {i+1}: {evento}")
        else:
            print(f"❌ No se pudo obtener evento en consulta {i+1}")
        time.sleep(intervalo)

if __name__ == "__main__":
    print(f"🚀 Iniciando generador de tráfico usando distribución: {DISTRIBUCION}")
    generar_trafico()
