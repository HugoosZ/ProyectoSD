import time
from waze_scraper import obtener_eventos
import sys
import os

# Asegurarnos que el path al módulo storage esté disponible
sys.path.append(os.path.join(os.path.dirname(__file__), '../../storage/src'))

from mongo_storage import MongoStorage

def main():
    storage = MongoStorage()

    while True:
        print("\n⏱️ Scrapeando eventos...")
        eventos = obtener_eventos()
        storage.guardar_eventos(eventos)
        time.sleep(120) # Espera de 2 minutos entre cada scrapeo

if __name__ == "__main__":
    main()
