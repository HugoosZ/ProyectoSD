import os
import time
import json
from cache_manager import RedisCache

# Configurar directorio de datos compartidos
DATA_DIR = "/app/shared-data/query_results"

def main():
    
    # Esperar flag de datos procesados antes de procesar
    if not esperar_flag_datos_listos():
        return
    
    eliminar_flag_datos_listos()
    print("Iniciando carga de datos en cache")
    
    # Crear instancia de RedisCache
    cache = RedisCache()
    
    # Verificar que los datos están disponibles
    if not verificar_datos_disponibles(DATA_DIR):
        print("Datos no disponibles o inválidos")
        return
    
    # Intentar cargar datos en Redis
    try:
        print(f"Cargando datos desde: {DATA_DIR}")
        
        if cache.enviar_resultados_a_cache(DATA_DIR):
            print("Datos cargados exitosamente en Redis")
        else:
            print("Error al cargar datos en Redis")
            
    except Exception as e:
        print(f"Error durante la carga: {str(e)}")
        import traceback
        traceback.print_exc()

def esperar_flag_datos_listos(max_intentos=60, intervalo=10):
    """
    Esperar a que aparezca el flag que indica que los datos están listos
    """
    flag_path = '/app/shared-data/data_ready_cache.flag'
    
    print(f"   Flag esperado: {flag_path}")
    
    for intento in range(max_intentos):
        try:
            if os.path.exists(flag_path):
                # Leer información del flag
                with open(flag_path, 'r', encoding='utf-8') as f:
                    flag_info = json.load(f)
                
                return True
            
            print(f"   Intento {intento + 1}/{max_intentos} - Flag no encontrado, esperando {intervalo}s...")
            time.sleep(intervalo)
            
        except Exception as e:
            print(f"   Error verificando flag (intento {intento + 1}): {e}")
            time.sleep(intervalo)
    
    print(f"❌ Timeout: Cache-service no encontró flag después de {max_intentos * intervalo} segundos")
    return False


def verificar_datos_disponibles(directorio):
    """
    Verificar que los datos CSV estén disponibles y sean válidos
    """
    try:
        if not os.path.exists(directorio):
            print(f"Directorio no existe: {directorio}")
            return False
        
        archivos = os.listdir(directorio)
        archivos_csv = [f for f in archivos if f.endswith('.csv')]
        
        if not archivos_csv:
            print(f"No se encontraron archivos CSV en: {directorio}")
            return False
        
        print(f"Encontrados {len(archivos_csv)} archivos CSV:")
        for archivo in archivos_csv:
            archivo_path = os.path.join(directorio, archivo)
            tamaño = os.path.getsize(archivo_path)
            print(f"   - {archivo} ({tamaño:,} bytes)")
        
        return len(archivos_csv) > 0
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False
    
def eliminar_flag_datos_listos():
    """
    Eliminar el flag una vez que se han procesado los datos
    """
    flag_path = '/app/shared-data/data_ready_cache.flag'
    
    try:
        if os.path.exists(flag_path):
            os.remove(flag_path)
        else:
            print(f"Flag no encontrado para eliminar: {flag_path}")
    except Exception as e:
        print(f"Error eliminando flag: {e}")

if __name__ == "__main__":
    main()