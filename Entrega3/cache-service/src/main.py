import os
import time
from cache_manager import RedisCache

# Configurar directorio de datos compartidos
DATA_DIR = "/app/shared-data/query_results"

def main():
    # Crear instancia de RedisCache
    cache = RedisCache()
    
    # Sistema de reintentos para esperar datos
    max_intentos = 30
    for intento in range(max_intentos):
        try:
            # Verificar si el directorio existe y tiene archivos
            if os.path.exists(DATA_DIR) and os.listdir(DATA_DIR):
                print(f"📂 Datos encontrados en: {DATA_DIR}")
                
                # Enviar datos directamente a Redis
                if cache.enviar_resultados_a_cache(DATA_DIR):
                    print("🚀 Datos cargados exitosamente en Redis")
                    return
                else:
                    print("⚠️ Error al cargar datos en Redis")
                    break
            
            # Esperar si no hay datos aún
            if intento < max_intentos - 1:
                print(f"⏳ Esperando datos... (intento {intento+1}/{max_intentos})")
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ Error en intento {intento+1}: {str(e)}")
            time.sleep(10)
    
    print("🛑 Tiempo de espera agotado. No se encontraron datos.")

if __name__ == "__main__":
    main()