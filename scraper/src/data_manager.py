import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoDBManager:
    client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
    print("Conectando a MongoDB...")
    

# Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Conexion a MongoDB exitosa")
    except Exception as e:
        print(e)

    def insert_data(self, collection_name, data):
        collection = self.db[collection_name]
        return collection.insert_many(data)