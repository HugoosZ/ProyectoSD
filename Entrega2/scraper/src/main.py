import time
from waze_scraper import obtener_eventos
import sys
import os

sys.path.insert(0, "/app/storage")
from mongo_storage import MongoStorage


def main():
    storage = MongoStorage()

    while True:
        #print("\n Scrapeando eventos...")
        #eventos = obtener_eventos()
        #storage.guardar_eventos(eventos)
        time.sleep(120) # Espera de 2 minutos entre cada scrapeo

if __name__ == "__main__":
    main()
