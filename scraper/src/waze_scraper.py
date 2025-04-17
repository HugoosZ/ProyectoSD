import requests
import time
from datetime import datetime

# Coordenadas de Región Metropolitana
URL = "https://www.waze.com/live-map/api/georss"
PARAMS = {
    "top": -33.182467560110695,
    "bottom": -33.66043364754692,
    "left": -70.89892476797105,
    "right": -70.45397847890855,
    "env": "row",
    "types": "alerts,traffic"
}
#https://www.waze.com/live-map/api/georss?top=-33.182467560110695&bottom=-33.66043364754692&left=-70.89892476797105&right=-70.45397847890855&env=row&types=alerts,traffic
# Diccionario para almacenar eventos únicos
eventos_unicos = {}

def obtener_eventos():
    response = requests.get(URL, params=PARAMS)
    if response.status_code != 200:
        print("❌ Error al obtener datos")
        return

    data = response.json()
    for alerta in data.get("alerts", []):
        clave = f"{alerta.get('type')}_{alerta['location']['y']}_{alerta['location']['x']}_{alerta.get('subtype')}"
        hora = datetime.fromtimestamp(alerta.get("pubMillis", 0)/1000).isoformat()

        nuevo_evento = {
            "tipo": alerta.get("type"),
            "subtipo": alerta.get("subtype"),
            "ubicacion": alerta.get("street"),
            "ciudad": alerta.get("city"),
            "hora": hora,
            "lat": alerta["location"]["y"],
            "lon": alerta["location"]["x"]
        }

        # Si no existe el evento o cambió la hora se actualiza
        if clave not in eventos_unicos or eventos_unicos[clave]["hora"] != hora:
            eventos_unicos[clave] = nuevo_evento
            print("🆕 Evento nuevo o actualizado:", nuevo_evento)

# Loop de consulta cada 2 minutos (puedes cambiarlo)
while True:
    print(f"\n⏱️ Consultando eventos... {datetime.now().isoformat()}")
    obtener_eventos()
    time.sleep(60)