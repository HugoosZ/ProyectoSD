import time
import sys
import json
from datetime import datetime



sys.path.insert(0, "/storage/src")
from mongo_storage import MongoStorage

mongo = MongoStorage()


def procesar_con_pig(eventos):
    """Simula el procesamiento con Pig (versión simplificada)"""
    print("\n⚙️ Procesando datos con Pig (simulación)...")
    
    # Aquí iría tu lógica real con Pig
    # Por ahora simulamos algunas operaciones básicas
    
    # 1. Conteo por tipo de incidente
    conteo_tipos = {}
    for evento in eventos:
        tipo = evento.get('type', 'DESCONOCIDO')
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1
    
    # 2. Agrupación por comuna
    comunas = set(e.get('comuna', 'SIN_COMUNA') for e in eventos)
    
    print("📊 Resultados del procesamiento:")
    print(f" - Total eventos procesados: {len(eventos)}")
    print(" - Conteo por tipo de incidente:")
    for tipo, count in conteo_tipos.items():
        print(f"   - {tipo}: {count}")
    print(f" - Comunas encontradas: {len(comunas)}")
    
    return True

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
    

    # 3. Obtener todos los eventos
    print("\n📥 Obteniendo eventos desde MongoDB...")
    mongo = MongoStorage()
    eventos = mongo.obtener_todos_los_eventos()
    
    if not eventos:
        print("❌ No se pueden procesar eventos vacíos")
        return
    
    # 4. Exportar datos para Pig (formato JSON)
    if not exportar_datos_para_pig(eventos):
        return
    
    # 5. Procesar datos (simulación de Pig)
    if not procesar_con_pig(eventos):
        return
    
    print("\n" + "="*50)
    print("  VERIFICACIÓN COMPLETADA CON ÉXITO")
    print("="*50)

if __name__ == "__main__":
    main()