import time
import sys

sys.path.insert(0, "/storage/src")
from mongo_storage import MongoStorage

mongo = MongoStorage()

def main():
    print("owo")
    # a = mongo.obtener_todos_los_eventos()
    
    while True:

        time.sleep(120) # Espera de 2 minutos entre cada scrapeo

if __name__ == "__main__":
    main()
