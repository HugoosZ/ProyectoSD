import time
import sys
import json
import subprocess
from datetime import datetime
import os
import csv
import shutil

sys.path.insert(0, "/app/storage")
from mongo_storage import MongoStorage


# Verifica si Hadoop está listo antes de seguir
# Intenta varias veces por si tarda en levantar

def verificar_hadoop(max_intentos=500, espera_entre_intentos=10):
    print("\nVerificando conexión con Hadoop")
    for intento in range(max_intentos):
        try:
            resultado = subprocess.run("hdfs dfsadmin -report", shell=True, capture_output=True, text=True)
            if resultado.returncode == 0:
                print("Conexión con Hadoop establecida correctamente")
                return True
            else:
                print(f"Intento {intento + 1}/{max_intentos} fallido:")
                print(resultado.stderr)
                if intento < max_intentos - 1:
                    print(f"Esperando {espera_entre_intentos} segundos antes del siguiente intento")
                    time.sleep(espera_entre_intentos)
        except Exception as e:
            print(f"Intento {intento + 1}/{max_intentos} fallido: {str(e)}")
            if intento < max_intentos - 1:
                print(f"Esperando {espera_entre_intentos} segundos antes del siguiente intento")
                time.sleep(espera_entre_intentos)
    print("No se pudo establecer conexión con Hadoop después de varios intentos")
    return False

# Crea la carpeta principal en HDFS donde se guardan los datos procesados

def crear_directorios_hdfs():
    print("\nCreando directorios en HDFS")
    try:
        subprocess.run("hdfs dfs -mkdir -p /processing", shell=True, check=True)
        print("Directorios creados correctamente")
        return True
    except Exception as e:
        print(f"Error al crear directorios: {str(e)}")
        return False

# Ejecuta los scripts de Pig para limpiar, agrupar y analizar los datos
# También descarga los resultados a la carpeta local

def procesar_con_pig():
    print("\nProcesando datos con Apache Pig")
    try:
        # Limpia los datos viejos en HDFS
        subprocess.run("hdfs dfs -rm -f /processing/data_for_pig.csv", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/filtered_events", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/data_unique", shell=True)  
        subprocess.run("hdfs dfs -rm -r -f /processing/group_data", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/event_counts", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/incidentes_por_comuna", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/incidentes_ciudad_tipo", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/evolucion_temporal_diaria", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/evolucion_por_tipo", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/distribucion_horaria", shell=True)
        subprocess.run("hdfs dfs -rm -r -f /processing/picos_por_hora_tipo", shell=True)
        # Sube el CSV a HDFS
        subprocess.run("hdfs dfs -put /app/processing/src/data_for_pig.csv /processing/", shell=True, check=True)
        # Filtra los datos 
        print("\nEjecutando filtrado de datos con Pig")
        comando_filtrado = "pig -f /app/processing/src/pig/filtering.pig"
        resultado_filtrado = subprocess.run(comando_filtrado, shell=True, capture_output=True, text=True)
        if resultado_filtrado.returncode != 0:
            print("Error en el filtrado con Pig")
            print(resultado_filtrado.stderr)
            return False
        print("\nEjecutando agrupación y deduplicación de datos con Pig")
        # Agrupa y elimina duplicados
        comando_processing = "pig -f /app/processing/src/pig/group.pig"
        resultado_processing = subprocess.run(comando_processing, shell=True, capture_output=True, text=True)
        if resultado_processing.returncode != 0:
            print("Error en el procesamiento con Pig")
            print(resultado_processing.stderr)
            return False
        print("\nEjecutando análisis exploratorio con Pig")
        # Hace análisis exploratorio
        comando_analisis = "pig -f /app/processing/src/pig/processing.pig"
        resultado_analisis = subprocess.run(comando_analisis, shell=True, capture_output=True, text=True)
        if resultado_analisis.returncode != 0:
            print("Error en el análisis exploratorio con Pig")
            print(resultado_analisis.stderr)
            return False
        # Descarga los resultados a la carpeta local
        for results_dir in [
            '/processing/filtered_events',
            '/processing/data_unique',
            '/processing/event_counts',
            '/processing/incidentes_por_comuna',
            '/processing/incidentes_ciudad_tipo',
            '/processing/evolucion_temporal_diaria',
            '/processing/evolucion_por_tipo',
            '/processing/distribucion_horaria',
            '/processing/picos_por_hora_tipo'
        ]:
            local_results_path = results_dir.replace('/processing', '/app/processing/results')
            if os.path.exists(local_results_path):
                print(f"Carpeta {local_results_path} ya existe. Eliminando para evitar conflictos")
                shutil.rmtree(local_results_path)
            subprocess.run(f"hdfs dfs -get {results_dir} /app/processing/results/", shell=True, check=True)
            print(f"Resultados guardados en {local_results_path}")
        print("Procesamiento completado exitosamente")
        return True
    except Exception as e:
        print(f"Error al ejecutar Pig: {str(e)}")
        return False

# Exporta los datos a un CSV para que Pig los pueda leer

def exportar_datos_para_pig(eventos, archivo_salida='/app/processing/src/data_for_pig.csv'):
    print("\nExportando datos para Pig (CSV)")
    try:
        if not eventos:
            print("No hay eventos para exportar")
            return False
        campos = [k for k in eventos[0].keys() if k != '_id']
        with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for evento in eventos:
                evento = dict(evento)
                evento.pop('_id', None)
                writer.writerow({k: evento.get(k, '') for k in campos})
        print(f"Datos exportados correctamente en {archivo_salida}")
        return True
    except Exception as e:
        print(f"Error al exportar datos: {str(e)}")
        return False

# Espera a que Hadoop salga de safe mode antes de seguir

def esperar_salida_safe_mode(intervalo=10, max_intentos=30):
    print("\nEsperando a que Hadoop salga de safe mode")
    for intento in range(max_intentos):
        resultado = subprocess.run("hdfs dfsadmin -safemode get", shell=True, capture_output=True, text=True)
        if "Safe mode is OFF" in resultado.stdout:
            print("Safe mode desactivado. Continuando con el procesamiento")
            return True
        else:
            print(f"Safe mode aún activo (intento {intento+1}/{max_intentos}). Esperando {intervalo} segundos...")
            time.sleep(intervalo)
    print("Safe mode sigue activo después de varios intentos. Abortando procesamiento")
    return False

# Guarda todos los datos procesados en volumen compartido para elastic
def guardar_datos_para_elastic():
    import shutil
    
    print("\nCopiando todos los datos procesados para el contenedor elastic")
    try:
        # Directorio de destino para todos los archivos
        directorio_destino = '/app/shared-data/data'
        
        # Crear directorio si no existe
        os.makedirs(directorio_destino, exist_ok=True)
        print(f"Directorio de destino creado/verificado: {directorio_destino}")
        
        # Mapeo de resultados a copiar
        archivos_a_copiar = {
            'data_unique': 'data_unique.csv'
        }
        
        archivos_copiados = 0
        
        for carpeta_resultado, nombre_archivo in archivos_a_copiar.items():
            archivo_origen = f'/app/processing/results/{carpeta_resultado}/part-r-00000'
            archivo_destino = os.path.join(directorio_destino, nombre_archivo)
            
            if os.path.exists(archivo_origen):
                shutil.copy2(archivo_origen, archivo_destino)
                print(f"  ✓ {carpeta_resultado} -> {nombre_archivo}")
                archivos_copiados += 1
            else:
                print(f"  ✗ No encontrado: {archivo_origen}")
        
        # También copiar filtered_events si existe
        archivo_filtered = '/app/processing/results/filtered_events/part-m-00000'
        if os.path.exists(archivo_filtered):
            shutil.copy2(archivo_filtered, os.path.join(directorio_destino, 'filtered_events.csv'))
            print(f"  ✓ filtered_events -> filtered_events.csv")
            archivos_copiados += 1
        
        print(f"\nTotal de archivos copiados: {archivos_copiados}")
        
        if archivos_copiados > 0:
            print(f"Todos los datos procesados disponibles en: {directorio_destino}")

            data_unique = '/app/shared-data/data/data_unique.csv'
            if os.path.exists(data_unique):
            # Crear flag para indicar que los datos están listos
                crear_flag_datos_listos()
            return True
        else:
            print("No se pudo copiar ningún archivo de resultados")
            return False
        
    except Exception as e:
        print(f"Error copiando datos para elastic: {str(e)}")
        return False


def crear_flag_datos_listos():
    """Crear archivo flag para indicar que los datos están listos para elastic"""
    try:
        flag_path = '/app/shared-data/data_ready.flag'
        flag_info = {
            "timestamp": datetime.now().isoformat(),
            "status": "data_ready",
            "message": "Datos procesados listos para Elasticsearch"
        }
        
        with open(flag_path, 'w', encoding='utf-8') as f:
            json.dump(flag_info, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error creando flag: {e}")

# Orquesta todo el procesamiento

def main():
    storage = MongoStorage()
    ruta_csv = os.path.join('/app/processing/src', 'data_for_pig.csv')
    storage.obtener_todos_los_eventos(ruta_csv=ruta_csv)
    print("\n" + "="*50)
    print("  INICIO DE VERIFICACIÓN DEL SISTEMA")
    print("="*50)
    # Primero revisa que Hadoop esté listo
    if not verificar_hadoop():
        print("No se pudo establecer conexión con Hadoop. Saliendo")
        sys.exit(1)
    if not esperar_salida_safe_mode():
        print("Hadoop sigue en safe mode. Saliendo")
        sys.exit(1)
    if not crear_directorios_hdfs():
        print("No se pudieron crear los directorios en HDFS. Saliendo")
        sys.exit(1)
    print("\nIniciando procesamiento de datos")
    if procesar_con_pig():
        print("Procesamiento completado exitosamente")
        guardar_datos_para_elastic()
    else:
        print("Error en el procesamiento")
        sys.exit(1)


if __name__ == "__main__":
    main()