import os
from pymongo import MongoClient
from dotenv import load_dotenv
import random 
import numpy as np
load_dotenv(dotenv_path='mongo.env')

class MongoStorage:
    def __init__(self):
        print("MongoStorage inicializado correctamente")  
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("No se encontró la variable de entorno MONGO_URI")
        self.client = MongoClient(mongo_uri)
        self.db = self.client["waze_traffic"]
        self.collection = self.db["events"]

    def guardar_eventos(self, eventos):
        if not eventos:
            print("No hay eventos para guardar")
            return
        try:
            self.collection.insert_many(eventos)
            print(f"Se insertaron {len(eventos)} eventos")
        except Exception as e:
            print("Error al insertar eventos:", e)

    def obtener_eventos(self, limite=10):
        try:
            if limite:
                eventos = list(self.collection.find().limit(limite))
            else:
                eventos = list(self.collection.find())
            print(f"Se obtuvieron {len(eventos)} eventos de la base de datos")
            return eventos
        except Exception as e:
            print("Error al obtener eventos:", e)
            return []

    def obtener_evento_uniforme(self):
        total = self.collection.count_documents({})
        if total == 0:
            print("No hay eventos almacenados")
            return None
        skip = random.randint(0, total - 1)
        return self.collection.find().skip(skip).limit(1).next()
    
    def obtener_evento_exponencial(self,cantidad):
        if cantidad == 0:
            return None
        beta = cantidad / 5  # Valor ajustable para obtener concentraciones distintas 
        while True:
            raw = int(np.random.exponential(scale=beta))
            if raw < cantidad:
                break
        return self.collection.find().skip(raw).limit(1).next()
    
    def obtener_todos_los_eventos(self, ruta_csv=None):
        try:
            eventos = list(self.collection.find())
            if not eventos:
                print("No se encontraron eventos en la base de datos")
                return []
            print(f"Total de eventos recuperados: {len(eventos)}")
            # Si se pasa una ruta, guardar el CSV
            if ruta_csv:
                import csv
                campos = [k for k in eventos[0].keys() if k != '_id']
                with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=campos)
                    writer.writeheader()
                    for evento in eventos:
                        evento = dict(evento)
                        evento.pop('_id', None)
                        writer.writerow({k: evento.get(k, '') for k in campos})
                print(f"Eventos guardados en {ruta_csv}")
            return eventos
        except Exception as e:
            print("Error al recuperar todos los eventos:", e)
            return []