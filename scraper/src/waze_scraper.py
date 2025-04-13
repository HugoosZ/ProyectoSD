#from scraper.src.data_manager import MongoDBManager

# Uso ejemplo
#db_manager = MongoDBManager()
#db_manager.insert_data("traffic_events", datos_extraidos)


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import pandas as pd
from datetime import datetime
import time


def configurar_driver():
    opciones = Options()
    opciones.add_argument("--headless")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")
    opciones.add_argument("--disable-gpu")
    opciones.add_argument("--window-size=1920,1080")
    
    # Usar el chromium del sistema
    driver = webdriver.Chrome(
        service=Service(executable_path='/usr/bin/chromedriver'), 
        options=opciones
    )
    return driver

# Prueba paso 1:
# Ejecuta esta función para asegurarte de que Selenium abre Chrome correctamente
def test_driver():
    driver = configurar_driver()
    driver.get("https://www.google.com")
    time.sleep(2)  # Esperar que cargue

    titulo = driver.title
    if "Google" in titulo:
        print("✅ Selenium abrió Google correctamente dentro del contenedor")
    else:
        print("❌ Hubo un problema, título inesperado:", titulo)

    driver.quit()