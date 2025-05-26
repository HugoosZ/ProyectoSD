import json
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv(dotenv_path='mongo.env')

# Conectar a MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client.traffic_db
collection = db.raw_incidents

def clean_data():
    # Eliminar registros incompletos y duplicados
    collection.delete_many({"tipo": {"$exists": False}})
    collection.delete_many({"ciudad": {"$regex": "\\u"}})  # Eliminar codificación incorrecta
    
    # Normalizar ciudades (ej: "Conchal\u00ed" -> "Conchalí")
    pipeline = [
        {"$addFields": {
            "ciudad": {"$replaceOne": {"input": "$ciudad", "find": "\\u00ed", "replacement": "í"}}
        }},
        {"$out": "clean_incidents"}
    ]
    collection.aggregate(pipeline)

if __name__ == "__main__":
    clean_data()