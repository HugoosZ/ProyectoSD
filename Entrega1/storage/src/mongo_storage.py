import os
from pymongo import MongoClient
from dotenv import load_dotenv
import random 
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

    def obtener_evento_aleatorio(self):
        total_documentos = self.collection.estimated_document_count()
        if total_documentos == 0:
            print("⚠️ No hay eventos almacenados")
            return None

        indice_aleatorio = random.randint(0, total_documentos - 1)
        evento = self.collection.find().skip(indice_aleatorio).limit(1)
        for doc in evento:
            return doc
        return None