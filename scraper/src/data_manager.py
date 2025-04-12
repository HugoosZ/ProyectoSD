import os
from pymongo import MongoClient

class MongoDBManager:
    def __init__(self):
        self.client = MongoClient(
            host=os.getenv("MONGO_HOST", "mongo"),
            port=int(os.getenv("MONGO_PORT", 27017)),
            username=os.getenv("MONGO_USER", "waze_user"),
            password=os.getenv("MONGO_PASSWORD", "securepassword"),
            authSource=os.getenv("MONGO_DB", "waze_events")
        )
        self.db = self.client[os.getenv("MONGO_DB", "waze_events")]
        
    def insert_data(self, collection_name, data):
        collection = self.db[collection_name]
        return collection.insert_many(data)