import redis
import os
import json
from datetime import datetime
import pandas as pd

class RedisCache:
    def __init__(self):
        """Inicializa RedisCache usando variables de entorno"""
        print("RedisCache inicializado correctamente")
        
        # Obtener configuración de variables de entorno
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        
        print(f"Conectando a Redis: {self.redis_host}:{self.redis_port}")
        
        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True,
            socket_connect_timeout=5
        )
        self._test_connection()

    def _test_connection(self):
        """Verifica que Redis esté accesible."""
        try:
            self.client.ping()
            print("Conexión a Redis exitosa")
        except redis.ConnectionError as e:
            raise RuntimeError(f"Error conectando a Redis: {e}")

    def enviar_resultados_a_cache(self, data_folder_path):
        """Envía todos los resultados procesados a Redis Cache"""
        if not os.path.exists(data_folder_path):
            print(f"Directorio no encontrado: {data_folder_path}")
            return False
        
        archivos_procesados = 0
        total_documentos = 0
        
        # Procesar cada archivo CSV en el directorio
        for file_name in os.listdir(data_folder_path):
            if file_name.endswith(".csv"):
                file_path = os.path.join(data_folder_path, file_name)
                print(f"\nProcesando archivo: {file_name}")
                
                # Determinar tipo de archivo y clave de caché
                cache_key, schema = self._determinar_esquema(file_name)
                
                if not cache_key:
                    print(f"Tipo de archivo no reconocido: {file_name}")
                    continue
                
                # Leer archivo CSV
                df = pd.read_csv(file_path, names=schema)
                
                # Convertir a formato JSON para caché
                for _, row in df.iterrows():
                    documento = row.to_dict()
                    documento['@timestamp'] = datetime.now().isoformat()
                    
                    # Crear clave única basada en contenido
                    unique_key = f"{cache_key}:{hash(frozenset(documento.items()))}"
                    self.client.hset(cache_key, unique_key, json.dumps(documento))
                
                print(f"Documentos cargados en '{cache_key}': {len(df)}")
                archivos_procesados += 1
                total_documentos += len(df)
        
        # Guardar estadísticas de caché
        stats = {
            "archivos_procesados": archivos_procesados,
            "total_documentos": total_documentos,
            "redis_host": self.redis_host,
            "redis_port": self.redis_port,
            "ultima_actualizacion": datetime.now().isoformat()
        }
        self.client.set("cache:estadisticas", json.dumps(stats))
        
        print(f"\nCarga completada: {archivos_procesados} archivos, {total_documentos} documentos")
        return True

    def _determinar_esquema(self, file_name):
        """Determina esquema y clave de caché según tipo de archivo"""
        # Mapeo actualizado para reconocer los archivos reales
        if "incidentes_ciudad_tipo" in file_name or "incidentes_por_ciudad" in file_name:
            return "incidentes:por_ciudad", ['comuna', 'tipo', 'conteo']
        
        elif "conteo_eventos" in file_name or "event_counts" in file_name:
            return "incidentes:global", ['tipo', 'conteo']
        
        elif "peak_por_horario" in file_name or "distribucion_horaria" in file_name or "picos_por_hora_tipo" in file_name:
            return "incidentes:horarios", ['hora', 'tipo', 'conteo']
        
        elif "incidente_por_comuna" in file_name or "incidentes_por_comuna" in file_name:
            return "incidentes:resumen_comunas", ['comuna', 'total', 'dummy']
        
        # Nuevos patrones para archivos adicionales
        elif "no_processing_data" in file_name:
            return "datos:sin_procesar", ['tipo', 'subtipo', 'calle', 'comuna', 'fecha', 'latitud', 'longitud']
        
        elif "filtered_events" in file_name:
            return "datos:filtrados", ['tipo', 'subtipo', 'calle', 'comuna', 'fecha', 'latitud', 'longitud']
        
        elif "data_unique" in file_name:
            return "datos:unicos", ['tipo', 'subtipo', 'calle', 'comuna', 'fecha', 'latitud', 'longitud']
        
        elif "evolucion_temporal_diaria" in file_name:
            return "analisis:evolucion_diaria", ['fecha', 'cantidad']
        
        elif "evolucion_por_tipo" in file_name:
            return "analisis:evolucion_tipo", ['fecha', 'tipo_evento', 'cantidad']
        
        return None, None