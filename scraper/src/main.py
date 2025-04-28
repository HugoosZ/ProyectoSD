import time
from waze_scraper import obtener_eventos
import sys
import os

# El módulo storage está instalado via pip, no necesitamos agregar un path
# El import debería funcionar directamente


# scraper/src/main.py

import sys
sys.path.insert(0, "/storage/src")

from mongo_storage import MongoStorage

mongo_storage = MongoStorage()



def main():
    storage = MongoStorage()

    while True:
        print("\n⏱️ Scrapeando eventos...")
        eventos = obtener_eventos()
        storage.guardar_eventos(eventos)
        time.sleep(120) # Espera de 2 minutos entre cada scrapeo

if __name__ == "__main__":
    main()
