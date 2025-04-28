import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(dotenv_path='mongo.env')

class MongoStorage:
    def __init__(self):
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
