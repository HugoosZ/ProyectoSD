import requests
from datetime import datetime

# Parámetros para el scraping
URL = "https://www.waze.com/live-map/api/georss"
PARAMS = {
    "top": -33.182467560110695,
    "bottom": -33.66043364754692,
    "left": -70.89892476797105,
    "right": -70.45397847890855,
    "env": "row",
    "types": "alerts,traffic"
}

def obtener_eventos():
    eventos = []
    response = requests.get(URL, params=PARAMS)
    if response.status_code != 200:
        print("❌ Error al obtener datos:", response.status_code)
        return eventos

    data = response.json()
    for alerta in data.get("alerts", []) + data.get("traffic", []):
        evento = {
            "tipo": alerta.get("type"),
            "subtipo": alerta.get("subtype"),
            "ubicacion": alerta.get("street"),
            "ciudad": alerta.get("city"),
            "hora": datetime.fromtimestamp(alerta.get("pubMillis", 0)/1000).isoformat(),
            "lat": alerta["location"]["y"],
            "lon": alerta["location"]["x"]
        }
        eventos.append(evento)
    return eventos
