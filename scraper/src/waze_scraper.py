#from scraper.src.data_manager import MongoDBManager

# Uso ejemplo
#db_manager = MongoDBManager()
#db_manager.insert_data("traffic_events", datos_extraidos)


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def cerrar_tooltip(driver):
    try:
        tooltip = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "waze-tour-tooltip__content"))
        )
        driver.execute_script("arguments[0].remove();", tooltip)
        print("✅ Tooltip eliminado")
    except:
        print("⚠️ Tooltip no presente (no se eliminó)")


def cerrar_overlay(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "waze-tour-step__overlay"))
        )
        print("🕵️ Overlay detectado")
        driver.execute_script("""
            const overlay = document.querySelector('.waze-tour-step__overlay');
            if (overlay) {
                overlay.remove();
            }
        """)
        print("✅ Overlay eliminado")
    except Exception as e:
        print("⚠️ No se pudo eliminar overlay:", e)


def obtener_eventos_waze(driver):
    print("❌ ")
    driver = configurar_driver()
    driver.get("https://www.waze.com/live-map")  # Accede al mapa en vivo de Waze
    cerrar_overlay(driver)
    cerrar_tooltip(driver)  # esta nueva
    time.sleep(10)  # Espera a que cargue el mapa y los elementos


    # Puedes mover el mapa a la Región Metropolitana si es necesario con JS o el driver
    # Por ahora asumimos que ya está en Santiago

    eventos = []

    marcadores = driver.find_elements(By.CLASS_NAME, "leaflet-marker-icon")

    for marcador in marcadores:
        try:
            marcador.click()
            time.sleep(1.5)  # Esperamos a que aparezca el popup

            tipo = driver.find_element(By.CLASS_NAME, "wm-alert-details__title").text
            ubicacion = driver.find_element(By.CLASS_NAME, "wm-alert-details__address").text
            publicacion = driver.find_element(By.CLASS_NAME, "wm-alert-details__time").text

            eventos.append({
                "tipo": tipo,
                "ubicacion": ubicacion,
                "hora": datetime.now().isoformat(),
                "publicacion": publicacion
                
            })

        except Exception as e:
            print(f"⚠️ No se pudo leer un evento: {e}")
            continue

    return eventos