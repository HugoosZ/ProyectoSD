import os
from pymongo import MongoClient
from dotenv import load_dotenv
import random 
import numpy as np
# Cargar variables de entorno
load_dotenv(dotenv_path='mongo.env')

class MongoStorage:
    def __init__(self):
        print("✅ MongoStorage inicializado correctamente.")  
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("❌ No se encontró la variable de entorno MONGO_URI")
        self.client = MongoClient(mongo_uri)
        self.db = self.client["waze_traffic"]
        self.collection = self.db["events"]

    def guardar_eventos(self, eventos):
        if not eventos:
            print("⚠️ No hay eventos para guardar.")
            return
        try:
            self.collection.insert_many(eventos)
            print(f"✅ Se insertaron {len(eventos)} eventos.")
        except Exception as e:
            print("❌ Error al insertar eventos:", e)

    def obtener_eventos(self, limite=10):
        try:
            if limite:
                eventos = list(self.collection.find().limit(limite))
            else:
                eventos = list(self.collection.find())
            
            print(f"✅ Se obtuvieron {len(eventos)} eventos de la base de datos.")
            return eventos
        except Exception as e:
            print("❌ Error al obtener eventos:", e)
            return []

    def obtener_evento_uniforme(self):
        total = self.collection.count_documents({})
        if total == 0:
            print("⚠️ No hay eventos almacenados")
            return None

        skip = random.randint(0, total - 1)
        return self.collection.find().skip(skip).limit(1).next()
    
    def obtener_evento_exponencial(self, beta=10): ###Todavia no termino esto pero podria funcionar

        total = self.collection.count_documents({})
        if total == 0:
            return None
        raw = np.random.exponential(scale=beta)
        skip = int(raw) % total
        return self.collection.find().skip(skip).limit(1).next()