import requests
import time
from datetime import datetime

# URL y parámetros de búsqueda en la API
URL = "https://www.waze.com/live-map/api/georss"
PARAMS = {
    "top": -33.182467560110695,
    "bottom": -33.66043364754692,
    "left": -70.89892476797105,
    "right": -70.45397847890855,
    "env": "row",
    "types": "alerts,traffic"
}

# Diccionario para guardar eventos únicos
eventos_unicos = {}

def obtener_eventos():
    eventos = []  # Lista donde vamos a guardar solo eventos nuevos o actualizados
    response = requests.get(URL, params=PARAMS)
    if response.status_code != 200:
        print("❌ Error al obtener datos:", response.status_code)
        return eventos

    data = response.json()

    for alerta in data.get("alerts", []) + data.get("traffic", []):
        # Crear la clave única para cada evento
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

        # Si no existe el evento o cambió su hora, se guardama y actualizama
        if clave not in eventos_unicos or eventos_unicos[clave]["hora"] != hora:
            eventos_unicos[clave] = nuevo_evento
            eventos.append(nuevo_evento)  # Solo nuevos eventos nuevos o actualizados
            print("🆕 Evento nuevo o actualizado:", nuevo_evento)

    return eventos

# Ejemplo de uso: hacer consulta cada 1 minuto
if __name__ == "__main__":
    while True:
        print(f"\n⏱️ Consultando eventos... {datetime.now().isoformat()}")
        nuevos_eventos = obtener_eventos()

        if nuevos_eventos:
            print(f"✅ Se encontraron {len(nuevos_eventos)} evento(s) nuevo(s) o actualizado(s).")
        else:
            print("⏸️ Sin cambios en los eventos.")

        time.sleep(60)  # Esperar 1 minuto