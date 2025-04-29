import time
from waze_scraper import obtener_eventos
import sys
import os

sys.path.insert(0, "/storage/src")
from mongo_storage import MongoStorage


def main():
    storage = MongoStorage()

    while True:
<<<<<<< HEAD
        #print("\n⏱️ Scrapeando eventos...")
        # eventos = obtener_eventos()
        # storage.guardar_eventos(eventos)
=======
        #print("\n⏱️ Scrapeando eventos...")
        #eventos = obtener_eventos()
        #storage.guardar_eventos(eventos)
>>>>>>> dabd4e391bd7c1790d62fe6bfab0c8f87f32645f
        time.sleep(120) # Espera de 2 minutos entre cada scrapeo

if __name__ == "__main__":
    main()
