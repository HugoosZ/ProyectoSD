import requests
import time
from datetime import datetime
from pymongo import MongoClient

# 1. Conexión a MongoDB Atlas
client = MongoClient(
    "MONGO_URI"
)
db = client["waze_traffic"]
collection = db["events"]

# 2. Parámetros de la Región Metropolitana
URL = "https://www.waze.com/live-map/api/georss"
PARAMS = {
    "top": -33.182467560110695,
    "bottom": -33.66043364754692,
    "left": -70.89892476797105,
    "right": -70.45397847890855,
    "env": "row",
    "types": "alerts,traffic"
}

# Diccionario para eventos únicos en memoria
eventos_unicos = {}

def obtener_eventos():
    # 3. Petición y parseo JSON :contentReference[oaicite:1]{index=1}
    response = requests.get(URL, params=PARAMS)
    if response.status_code != 200:
        print(f"❌ Error al obtener datos: {response.status_code}")  # validar status :contentReference[oaicite:2]{index=2}
        return

    data = response.json()
    # Procesamos tanto 'alerts' como 'traffic' si existen
    for alerta in data.get("alerts", []) + data.get("traffic", []):
        # Clave única según tipo, ubicación y subtipo
        lat = alerta["location"]["y"]
        lon = alerta["location"]["x"]
        clave = f"{alerta.get('type')}_{lat}_{lon}_{alerta.get('subtype')}"

        # Convertimos pubMillis a ISO
        hora = datetime.fromtimestamp(alerta.get("pubMillis", 0) / 1000).isoformat()

        nuevo_evento = {
            "tipo": alerta.get("type"),
            "subtipo": alerta.get("subtype"),
            "ubicacion": alerta.get("street"),
            "ciudad": alerta.get("city"),
            "hora": hora,
            "lat": lat,
            "lon": lon
        }

        # 4. Si es nuevo o cambió la hora, lo guardamos en memoria e insertamos en MongoDB
        if clave not in eventos_unicos or eventos_unicos[clave]["hora"] != hora:
            eventos_unicos[clave] = nuevo_evento
            try:
                collection.insert_one(nuevo_evento)
                print("🆕 Evento insertado en DB:", nuevo_evento)
            except Exception as e:
                print("❌ Error al insertar en MongoDB:", e)

if __name__ == "__main__":
    while True:
        print(f"\n⏱️ Consultando eventos… {datetime.now().isoformat()}")
        obtener_eventos()
        time.sleep(120)  # Espera 2 minutos antes de la siguiente consulta
