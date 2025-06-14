import time
from elasticsearch import Elasticsearch
import requests


def IntentoConexion():
    for i in range(10):
        try:
            es = Elasticsearch("http://elasticsearch:9200")
            if es.ping():
                print("Conexión a Elasticsearch exitosa.")
                break
            else:
                print("No se pudo conectar a Elasticsearch. Reintentando...")
        except Exception as e:
            print(f"Error al conectar a Elasticsearch: {e}")
        time.sleep(5)
    else:
        print("No se pudo conectar a Elasticsearch después de varios intentos.")

    # Intento de conexion para Kibana
    for i in range(10):
        try:
            response = requests.get("http://kibana:5601/api/status")
            if response.status_code == 200:
                print("Conexión a Kibana exitosa.")
                break
            else:
                print(f"No se pudo conectar a Kibana. Código: {response.status_code}. Reintentando...")
        except Exception as e:
            print(f"Error al conectar a Kibana: {e}")
        time.sleep(5)
    else:
        print("No se pudo conectar a Kibana después de varios intentos.")