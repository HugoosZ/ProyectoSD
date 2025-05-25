import time
import sys
import json
import subprocess
from datetime import datetime

def verificar_hadoop(max_intentos=5, espera_entre_intentos=10):
    """Verifica que Hadoop esté funcionando correctamente con reintentos"""
    print("\n🔍 Verificando conexión con Hadoop...")
    
    for intento in range(max_intentos):
        try:
            # Verificar que el namenode esté respondiendo
            resultado = subprocess.run("hdfs dfsadmin -report", shell=True, capture_output=True, text=True)
            if resultado.returncode == 0:
                print("✅ Conexión con Hadoop establecida correctamente")
                return True
            else:
                print(f"❌ Intento {intento + 1}/{max_intentos} fallido:")
                print(resultado.stderr)
                if intento < max_intentos - 1:
                    print(f"⏳ Esperando {espera_entre_intentos} segundos antes del siguiente intento...")
                    time.sleep(espera_entre_intentos)
        except Exception as e:
            print(f"❌ Intento {intento + 1}/{max_intentos} fallido: {str(e)}")
            if intento < max_intentos - 1:
                print(f"⏳ Esperando {espera_entre_intentos} segundos antes del siguiente intento...")
                time.sleep(espera_entre_intentos)
    
    print("❌ No se pudo establecer conexión con Hadoop después de varios intentos")
    return False

def crear_directorios_hdfs():
    """Crea los directorios necesarios en HDFS"""
    print("\n📁 Creando directorios en HDFS...")
    try:
        subprocess.run("hdfs dfs -mkdir -p /processing", shell=True, check=True)
        print("✅ Directorios creados correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear directorios: {str(e)}")
        return False

def procesar_con_pig(eventos):
    """Ejecuta el procesamiento con Apache Pig"""
    print("\n⚙️ Procesando datos con Apache Pig...")
    
    try:
        # Copiar el archivo JSON a HDFS
        subprocess.run("hdfs dfs -put /processing/data_for_pig.json /processing/", shell=True, check=True)
        
        # Ejecutar el script de Pig
        comando = "pig -f /processing/src/pig/remove_duplicates.pig"
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Procesamiento con Pig completado exitosamente")
            print("\n📊 Resultados del procesamiento:")
            print(resultado.stdout)
            
            # Copiar los resultados de vuelta al sistema de archivos local
            subprocess.run("hdfs dfs -get /processing/unique_data /processing/", shell=True, check=True)
            subprocess.run("hdfs dfs -get /processing/count_by_type /processing/", shell=True, check=True)
            subprocess.run("hdfs dfs -get /processing/sorted_data /processing/", shell=True, check=True)
            
            # Mostrar resumen de resultados
            print("\n📈 Resumen de resultados:")
            print("- Datos únicos guardados en /processing/unique_data")
            print("- Conteo por tipo guardado en /processing/count_by_type")
            print("- Datos ordenados guardados en /processing/sorted_data")
            
            return True
        else:
            print("❌ Error en el procesamiento con Pig:")
            print(resultado.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error al ejecutar Pig: {str(e)}")
        return False

def exportar_datos_para_pig(eventos, archivo_salida='/processing/data_for_pig.json'):
    """Exporta datos en formato compatible con Pig"""
    print("\n📤 Exportando datos para Pig...")
    try:
        with open(archivo_salida, 'w') as f:
            for evento in eventos:
                # Eliminamos _id que no es serializable
                evento.pop('_id', None)
                f.write(json.dumps(evento) + '\n')
        print(f"✅ Datos exportados correctamente en {archivo_salida}")
        return True
    except Exception as e:
        print(f"❌ Error al exportar datos: {str(e)}")
        return False

def main():
    print("\n" + "="*50)
    print("  INICIO DE VERIFICACIÓN DEL SISTEMA")
    print("="*50)
    
    # Verificar Hadoop
    if not verificar_hadoop():
        print("❌ No se pudo establecer conexión con Hadoop. Saliendo...")
        sys.exit(1)
    
    # Crear directorios en HDFS
    if not crear_directorios_hdfs():
        print("❌ No se pudieron crear los directorios en HDFS. Saliendo...")
        sys.exit(1)
    
    # Por ahora, solo mantenemos el sistema en ejecución
    print("\n✅ Sistema inicializado correctamente")
    print("🔄 Esperando datos para procesar...")
    
    while True:
        time.sleep(60)  # Esperar 1 minuto antes de la siguiente verificación

if __name__ == "__main__":
    main()