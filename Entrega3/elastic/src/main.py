import sys
import os
from conexion import IntentoConexion
import pandas as pd
from elasticsearch import Elasticsearch
from datetime import datetime

sys.path.insert(0, "/app/storage")
from mongo_storage import MongoStorage


def procesar_y_subir_csv(es, archivo_path, nombre_archivo):
    """Procesar un archivo CSV y subirlo a Elasticsearch"""
    try:
        print(f"\nProcesando archivo: {nombre_archivo}")
        
        # Obtener nombres de columnas específicos para cada tipo de archivo
        columnas = obtener_nombres_columnas(nombre_archivo)
        df = pd.read_csv(archivo_path, header=None, names=columnas)
        print(f"Filas leidas: {len(df)}")
        
        # Crear nombre del índice basado en el archivo
        indice_nombre = f"waze_{nombre_archivo.replace('.csv', '').replace('_', '-')}"
        print(f"Indice destino: {indice_nombre}")
        
        # Configurar mapeo específico según el tipo de datos
        mapeo = crear_mapeo_para_archivo(nombre_archivo, df)
        
        # Crear el índice si no existe
        if not es.indices.exists(index=indice_nombre):
            print(f"Creando indice: {indice_nombre}")
            configuracion_indice = crear_configuracion_indice()
            configuracion_indice["mappings"] = mapeo
            es.indices.create(index=indice_nombre, body=configuracion_indice)
        else:
            # Verificar si existe conflicto de mapeo (especialmente para location)
            try:
                current_mapping = es.indices.get_mapping(index=indice_nombre)
                location_type = None
                if indice_nombre in current_mapping:
                    props = current_mapping[indice_nombre].get('mappings', {}).get('properties', {})
                    if 'location' in props:
                        location_type = props['location'].get('type')
                
                # Si location no es geo_point, recrear el índice
                if location_type and location_type != 'geo_point':
                    print(f"Recreando indice por conflicto de mapeo...")
                    es.indices.delete(index=indice_nombre)
                    configuracion_indice = crear_configuracion_indice()
                    configuracion_indice["mappings"] = mapeo
                    es.indices.create(index=indice_nombre, body=configuracion_indice)
            except Exception as e:
                print(f"Error verificando mapeo: {e}")

        # Indexar documentos uno por uno con validación
        documentos_indexados = 0
        documentos_con_error = 0
        
        for index, row in df.iterrows():
            try:
                # Convertir fila a documento JSON
                doc = row.to_dict()
                
                # Limpiar y validar datos primero
                doc = limpiar_documento(doc)
                
                if not doc:
                    documentos_con_error += 1
                    continue
                
                # Usar la fecha del evento como @timestamp si existe, sino usar la actual
                if 'fecha' in doc and doc['fecha']:
                    try:
                        # Intentar usar la fecha del evento
                        fecha_evento = pd.to_datetime(doc['fecha'], errors='coerce')
                        if not pd.isna(fecha_evento):
                            doc['@timestamp'] = fecha_evento.isoformat()
                        else:
                            # Si no se puede parsear, usar timestamp actual
                            doc['@timestamp'] = datetime.now().isoformat()
                    except:
                        doc['@timestamp'] = datetime.now().isoformat()
                else:
                    # Si no hay fecha del evento, usar timestamp actual
                    doc['@timestamp'] = datetime.now().isoformat()
                
                # Solo indexar documentos válidos
                if doc:
                    es.index(index=indice_nombre, body=doc)
                    documentos_indexados += 1
                else:
                    documentos_con_error += 1
                    
            except Exception as e:
                print(f"Error indexando fila {index}: {e}")
                documentos_con_error += 1
                continue

        print(f"Documentos indexados: {documentos_indexados}/{len(df)}")
        if documentos_con_error > 0:
            print(f"Documentos con errores: {documentos_con_error}")
        return True
        
    except Exception as e:
        print(f"Error procesando {nombre_archivo}: {e}")
        return False


def crear_mapeo_para_archivo(nombre_archivo, df):
    """Crear mapeo específico según el tipo de archivo"""
    # Mapeo base común para todos los archivos
    mapeo_base = {
        "properties": {
            "@timestamp": {"type": "date"},
            "location": {"type": "geo_point"}  # Campo geo para mapas
        }
    }
    
    # Mapeos específicos según el tipo de archivo procesado
    if "event_counts" in nombre_archivo:
        mapeo_base["properties"].update({
            "tipo_evento": {"type": "keyword"},
            "cantidad": {"type": "integer"}
        })
    elif any(x in nombre_archivo for x in ["no_processing_data", "data_unique", "filtered_events"]):
        mapeo_base["properties"].update({
            "tipo": {"type": "keyword"},
            "subtipo": {"type": "keyword"},
            "calle": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "comuna": {"type": "keyword"},
            "fecha": {"type": "date"},
            "latitud": {"type": "float"},
            "longitud": {"type": "float"}
        })
    elif "distribucion_horaria" in nombre_archivo:
        mapeo_base["properties"].update({
            "hora": {"type": "integer"},
            "cantidad": {"type": "integer"}
        })
    elif "incidentes_por_comuna" in nombre_archivo:
        mapeo_base["properties"].update({
            "comuna": {"type": "keyword"},
            "cantidad_incidentes": {"type": "integer"},
            "porcentaje": {"type": "float"}
        })
    elif "evolucion_temporal_diaria" in nombre_archivo:
        mapeo_base["properties"].update({
            "fecha": {"type": "date"},
            "cantidad": {"type": "integer"}
        })
    elif "evolucion_por_tipo" in nombre_archivo:
        mapeo_base["properties"].update({
            "fecha": {"type": "date"},
            "tipo_evento": {"type": "keyword"},
            "cantidad": {"type": "integer"}
        })
    elif "incidentes_ciudad_tipo" in nombre_archivo:
        mapeo_base["properties"].update({
            "comuna": {"type": "keyword"},
            "tipo_evento": {"type": "keyword"},
            "cantidad": {"type": "integer"}
        })
    elif "picos_por_hora_tipo" in nombre_archivo:
        mapeo_base["properties"].update({
            "hora": {"type": "integer"},
            "tipo_evento": {"type": "keyword"},
            "cantidad": {"type": "integer"}
        })
    else:
        # Mapeo genérico basado en el análisis automático de tipos
        for col in df.columns:
            if df[col].dtype in ['int64', 'int32']:
                mapeo_base["properties"][col] = {"type": "integer"}
            elif df[col].dtype in ['float64', 'float32']:
                mapeo_base["properties"][col] = {"type": "float"}
            elif 'fecha' in col.lower() or 'date' in col.lower():
                mapeo_base["properties"][col] = {"type": "date"}
            else:
                # Text con keyword para aggregations
                mapeo_base["properties"][col] = {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                }
    
    return mapeo_base


def crear_configuracion_indice():
    """Crear configuración del índice para optimizar el rendimiento"""
    return {
        "settings": {
            "index": {
                "max_result_window": 50000,
                "max_docvalue_fields_search": 200
            }
        }
    }


def limpiar_documento(doc):
    """Limpiar y convertir tipos de datos en el documento"""
    doc_limpio = {}
    
    for key, value in doc.items():
        # Saltar valores nulos o vacíos
        if pd.isna(value) or value is None:
            continue
            
        # Manejar coordenadas geográficas
        if key in ['latitud', 'longitud', 'lat', 'lng', 'latitude', 'longitude']:
            try:
                doc_limpio[key] = float(value)
            except:
                continue
        # Manejar campos numéricos enteros
        elif key in ['cantidad', 'count', 'hora', 'hour']:
            try:
                doc_limpio[key] = int(value)
            except:
                continue
        # Manejar campos de fecha con validación
        elif 'fecha' in key.lower() or 'date' in key.lower():
            try:
                # Validar que sea una cadena válida
                if not isinstance(value, str) or not value.strip():
                    continue
                    
                # Filtrar valores que no son fechas reales
                valores_invalidos = ['hora', 'hour', 'fecha', 'date', 'time', 'n/a', 'null', 'none', '']
                if value.lower().strip() in valores_invalidos:
                    continue
                
                # Intentar parsear la fecha
                fecha_parseada = pd.to_datetime(value, errors='coerce')
                if pd.isna(fecha_parseada):
                    continue
                
                doc_limpio[key] = fecha_parseada.isoformat()
            except Exception:
                continue
        else:
            # Convertir todo lo demás a string
            doc_limpio[key] = str(value)
    
    # Crear campo geo_point para mapas si tenemos coordenadas válidas
    if 'latitud' in doc_limpio and 'longitud' in doc_limpio:
        try:
            lat = float(doc_limpio['latitud'])
            lon = float(doc_limpio['longitud'])
            # Validar rangos geográficos
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                doc_limpio['location'] = f"{lat},{lon}"
        except (ValueError, TypeError):
            pass
    
    return doc_limpio


def limpiar_indices_waze(es):
    """Eliminar todos los índices de Waze existentes para evitar duplicados"""
    try:
        print("\nLimpiando indices existentes...")
        indices_existentes = es.indices.get_alias(index="waze*")
        
        if indices_existentes:
            print(f"Eliminando {len(indices_existentes)} indices de Waze:")
            for indice in indices_existentes.keys():
                try:
                    es.indices.delete(index=indice)
                    print(f"  ✓ {indice}")
                except Exception as e:
                    print(f"  ✗ {indice}: {e}")
        else:
            print("No se encontraron indices de Waze existentes")
            
    except Exception as e:
        print(f"Error durante la limpieza de indices: {e}")


def subir_datasets_a_elasticsearch(data_folder_path):
    """Función principal para subir todos los datasets a Elasticsearch"""
    print("\nIniciando carga a Elasticsearch...")
    
    # Establecer conexión con Elasticsearch
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            print("No se pudo conectar a Elasticsearch")
            return False
        print("Conexion a Elasticsearch exitosa")
    except Exception as e:
        print(f"Error conectando a Elasticsearch: {e}")
        return False
    
    # Verificar que el directorio de datos existe
    if not os.path.exists(data_folder_path):
        print(f"Directorio no encontrado: {data_folder_path}")
        return False
    
    # Buscar archivos CSV para procesar (excluir datos sin procesar para evitar duplicados)
    archivos_csv = [f for f in os.listdir(data_folder_path) 
                    if f.endswith('.csv') and 'no_processing_data' not in f]
    
    if not archivos_csv:
        print(f"No se encontraron archivos CSV procesados en: {data_folder_path}")
        return False
    
    print(f"Archivos CSV procesados encontrados: {len(archivos_csv)}")
    
    # Procesar cada archivo encontrado (solo datos procesados)
    archivos_procesados = 0
    for archivo in archivos_csv:
        archivo_path = os.path.join(data_folder_path, archivo)
        if procesar_y_subir_csv(es, archivo_path, archivo):
            archivos_procesados += 1
    
    print(f"\nResumen: {archivos_procesados}/{len(archivos_csv)} archivos procesados exitosamente (sin incluir datos raw)")
    
    # Mostrar resumen de índices creados
    try:
        indices = es.indices.get_alias(index="waze*")
        print(f"\nTodos los índices de Waze:")
        for indice in sorted(indices.keys()):
            doc_count = es.count(index=indice)['count']
            print(f"   - {indice}: {doc_count} documentos")
    except Exception as e:
        print(f"Error listando indices: {e}")
    
    return archivos_procesados > 0


def obtener_nombres_columnas(nombre_archivo):
    """Obtener nombres de columnas apropiados según el tipo de archivo"""
    if "event_counts" in nombre_archivo:
        return ["tipo_evento", "cantidad"]
    elif "no_processing_data" in nombre_archivo:
        return ["tipo", "subtipo", "calle", "comuna", "fecha", "latitud", "longitud"]
    elif "data_unique" in nombre_archivo:
        return ["tipo", "subtipo", "calle", "comuna", "fecha", "latitud", "longitud"]
    elif "filtered_events" in nombre_archivo:
        return ["tipo", "subtipo", "calle", "comuna", "fecha", "latitud", "longitud"]
    elif "distribucion_horaria" in nombre_archivo:
        return ["hora", "cantidad"]
    elif "incidentes_por_comuna" in nombre_archivo:
        return ["comuna", "cantidad_incidentes", "porcentaje"]
    elif "evolucion_temporal_diaria" in nombre_archivo:
        return ["fecha", "cantidad"]
    elif "evolucion_por_tipo" in nombre_archivo:
        return ["fecha", "tipo_evento", "cantidad"]
    elif "incidentes_ciudad_tipo" in nombre_archivo:
        return ["comuna", "tipo_evento", "cantidad"]
    elif "picos_por_hora_tipo" in nombre_archivo:
        return ["hora", "tipo_evento", "cantidad"]
    else:
        # Nombres genéricos para archivos desconocidos
        return [f"campo_{i}" for i in range(10)]  # Asumiendo máximo 10 columnas




def verificar_datos_actualizados():
    """
    Verifica si los datos procesados están actualizados comparando
    si existen todos los índices procesados esperados en ES.
    Si falta algún índice, requiere recarga completa.
    """
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            print("Elasticsearch no disponible")
            return False
            
        # Solo verificar que existan los índices de datasets procesados clave
        indices_esperados = [
            'waze_data-unique',
            'waze_filtered-events', 
            'waze_distribucion-horaria'
        ]
        
        print("Verificando que existan todos los índices procesados...")
        
        for indice in indices_esperados:
            try:
                # Solo verificar que el índice existe y tiene datos
                response = es.count(index=indice)
                docs_es = response['count']
                
                if docs_es == 0:
                    print(f"Índice {indice} existe pero está vacío - se requiere recarga")
                    return False
                    
                print(f"  ✓ {indice}: {docs_es} documentos")
                
            except Exception as e:
                print(f"Índice {indice} no existe - se requiere carga completa")
                return False
                
        print("Todos los índices procesados están presentes y con datos")
        return True
        
    except Exception as e:
        print(f"Error verificando datos procesados: {e}")
        return False


def crear_data_views_kibana():
    """Crear Data Views automáticamente en Kibana para los índices de Waze"""
    import requests
    import time
    
    try:
        kibana_url = "http://kibana:5601"
        headers = {
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true'
        }
        
        # Verificar que Kibana esté disponible
        for intento in range(10):
            try:
                response = requests.get(f"{kibana_url}/api/status", headers=headers, timeout=5)
                if response.status_code == 200:
                    break
            except:
                if intento < 9:
                    time.sleep(3)
                else:
                    return False
        
        # Data Views a crear
        data_views = [
            {"title": "waze*", "name": "Waze - Todos los Datos", "timeFieldName": "@timestamp"},
            {"title": "waze_no-processing-data", "name": "Waze - Datos Sin Procesar", "timeFieldName": "@timestamp"},
            {"title": "waze_filtered-events", "name": "Waze - Eventos Filtrados", "timeFieldName": "@timestamp"},
            {"title": "waze_data-unique", "name": "Waze - Datos Únicos", "timeFieldName": "@timestamp"},
            {"title": "waze_distribucion-horaria", "name": "Waze - Distribución Horaria", "timeFieldName": "@timestamp"},
            {"title": "waze_event-counts", "name": "Waze - Conteo de Eventos", "timeFieldName": "@timestamp"},
            {"title": "waze_incidentes-por-comuna", "name": "Waze - Incidentes por Comuna", "timeFieldName": "@timestamp"}
        ]
        
        # Obtener data views existentes
        try:
            existing_response = requests.get(f"{kibana_url}/api/data_views", headers=headers, timeout=10)
            existing_titles = []
            if existing_response.status_code == 200:
                existing_data = existing_response.json()
                existing_titles = [dv['title'] for dv in existing_data.get('data_view', [])]
        except:
            existing_titles = []
        
        # Crear data views que no existan
        for dv in data_views:
            if dv["title"] not in existing_titles:
                try:
                    payload = {"data_view": dv}
                    requests.post(f"{kibana_url}/api/data_views/data_view", headers=headers, json=payload, timeout=10)
                except:
                    pass
                    
        return True
        
    except:
        return False


def realizar_consultas_estaticas():
    """Realizar consultas estáticas comparando datos procesados vs no procesados"""
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            print("Elasticsearch no disponible para consultas")
            return
            
        print("\n=== CONSULTAS ESTÁTICAS A ELASTICSEARCH ===")
        
        # Definir consultas estáticas para comparar
        consultas = [
            {
                "nombre": "Total de eventos por tipo",
                "query": {
                    "size": 0,
                    "aggs": {
                        "tipos": {
                            "terms": {
                                "field": "tipo",
                                "size": 10
                            }
                        }
                    }
                }
            },
            {
                "nombre": "Eventos por comuna (top 10)",
                "query": {
                    "size": 0,
                    "aggs": {
                        "comunas": {
                            "terms": {
                                "field": "comuna",
                                "size": 10
                            }
                        }
                    }
                }
            },
            {
                "nombre": "Distribución por subtipo",
                "query": {
                    "size": 0,
                    "aggs": {
                        "subtipos": {
                            "terms": {
                                "field": "subtipo",
                                "size": 10
                            }
                        }
                    }
                }
            },
            {
                "nombre": "Eventos en las últimas 24 horas",
                "query": {
                    "query": {
                        "range": {
                            "@timestamp": {
                                "gte": "now-24h"
                            }
                        }
                    },
                    "size": 0
                }
            },
            {
                "nombre": "Promedio de eventos por día",
                "query": {
                    "size": 0,
                    "aggs": {
                        "por_dia": {
                            "date_histogram": {
                                "field": "@timestamp",
                                "calendar_interval": "day"
                            }
                        }
                    }
                }
            }
        ]
        
        resultados_cache = {}
        
        for consulta in consultas:
            print(f"\n--- {consulta['nombre']} ---")
            
            # Consultar datos NO procesados
            try:
                resultado_raw = es.search(
                    index="waze_no-processing-data",
                    body=consulta["query"]
                )
                total_raw = resultado_raw['hits']['total']['value']
                print(f"📊 Datos NO procesados: {total_raw} documentos totales")
                
                # Mostrar agregaciones si existen
                if 'aggregations' in resultado_raw:
                    mostrar_agregaciones(resultado_raw['aggregations'], "  RAW")
                    
            except Exception as e:
                print(f"❌ Error en datos no procesados: {e}")
                resultado_raw = None
            
            # Consultar datos PROCESADOS (únicos)
            try:
                resultado_unique = es.search(
                    index="waze_data-unique",
                    body=consulta["query"]
                )
                total_unique = resultado_unique['hits']['total']['value']
                print(f"🔹 Datos PROCESADOS: {total_unique} documentos totales")
                
                # Mostrar agregaciones si existen
                if 'aggregations' in resultado_unique:
                    mostrar_agregaciones(resultado_unique['aggregations'], "  PROC")
                    
                # GUARDAR EN CACHÉ solo los datos procesados
                resultado_para_cache = {
                    'consulta': consulta['nombre'],
                    'total_documentos': total_unique,
                    'timestamp': datetime.now().isoformat(),
                    'agregaciones': resultado_unique.get('aggregations', {})
                }
                
                resultados_cache[consulta['nombre']] = resultado_para_cache
                
            except Exception as e:
                print(f"❌ Error en datos procesados: {e}")
                resultado_unique = None
            
            # Comparación
            if resultado_raw and resultado_unique:
                diferencia = total_raw - total_unique
                porcentaje_reduccion = (diferencia / total_raw * 100) if total_raw > 0 else 0
                print(f"📈 Diferencia: {diferencia} eventos ({porcentaje_reduccion:.1f}% reducción)")
        
        # Enviar resultados al caché
        if resultados_cache:
            enviar_a_cache(resultados_cache)
            
        print(f"\n✅ Consultas completadas. {len(resultados_cache)} resultados enviados a caché.")
        
    except Exception as e:
        print(f"Error en consultas estáticas: {e}")


def mostrar_agregaciones(aggs, prefijo=""):
    """Mostrar agregaciones de forma legible"""
    for key, value in aggs.items():
        if 'buckets' in value:
            print(f"{prefijo} {key}:")
            for bucket in value['buckets'][:5]:  # Solo mostrar top 5
                if 'key_as_string' in bucket:
                    print(f"{prefijo}   - {bucket['key_as_string']}: {bucket['doc_count']}")
                else:
                    print(f"{prefijo}   - {bucket['key']}: {bucket['doc_count']}")


def enviar_a_cache(datos):
    """Enviar datos procesados al servicio de caché Redis"""
    import requests
    import json
    
    try:
        cache_url = "http://waze-cache-service:8000"
        
        for nombre_consulta, resultado in datos.items():
            # Crear clave única para la consulta
            cache_key = f"consulta_estatica:{nombre_consulta.lower().replace(' ', '_')}"
            
            payload = {
                "key": cache_key,
                "value": json.dumps(resultado),
                "ttl": 3600  # 1 hora de TTL
            }
            
            try:
                response = requests.post(f"{cache_url}/set", json=payload, timeout=5)
                if response.status_code == 200:
                    print(f"💾 Guardado en caché: {nombre_consulta}")
                else:
                    print(f"⚠️  Error guardando en caché {nombre_consulta}: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error conectando al caché para {nombre_consulta}: {e}")
                
    except Exception as e:
        print(f"Error enviando datos al caché: {e}")


def obtener_desde_cache(nombre_consulta):
    """Obtener resultados desde el caché"""
    import requests
    import json
    
    try:
        cache_url = "http://waze-cache-service:8000"
        cache_key = f"consulta_estatica:{nombre_consulta.lower().replace(' ', '_')}"
        
        response = requests.get(f"{cache_url}/get/{cache_key}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('found'):
                return json.loads(data['value'])
        return None
        
    except Exception as e:
        print(f"Error obteniendo desde caché: {e}")
        return None


def main():
    # Verificar si los datos están actualizados comparando filas
    if verificar_datos_actualizados():
        print("\nDatos ya están actualizados - no se requiere carga")
        print("Elasticsearch y Kibana están disponibles en sus contenedores")
        
        # Realizar consultas estáticas incluso cuando los datos están actualizados
        realizar_consultas_estaticas()
        return
    
    print("\nIniciando carga completa de datos...")
    
    # Limpiar índices existentes de Waze antes de empezar
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if es.ping():
            limpiar_indices_waze(es)
    except Exception as e:
        print(f"Advertencia: Error en conexion inicial: {e}")
    
    # Exportar datos sin filtrar desde MongoDB
    storage = MongoStorage()
    os.makedirs('/app/elastic', exist_ok=True)
    os.makedirs('/app/shared-data/data', exist_ok=True)
    
    # Generar archivo en el directorio local del contenedor elastic
    ruta_csv_local = '/app/elastic/no_processing_data.csv'
    storage.obtener_todos_los_eventos(ruta_csv=ruta_csv_local)
    
    # También guardar en el directorio compartido para otros servicios
    ruta_csv_compartido = '/app/shared-data/data/no_processing_data.csv'
    storage.obtener_todos_los_eventos(ruta_csv=ruta_csv_compartido)
    print("Datos exportados de MongoDB (local y compartido)")
    
    # Subir datos sin filtrar a Elasticsearch
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if es.ping() and os.path.exists(ruta_csv_local):
            print("Subiendo datos sin filtrar...")
            procesar_y_subir_csv(es, ruta_csv_local, 'no_processing_data.csv')
    except Exception as e:
        print(f"Error subiendo datos sin filtrar: {e}")
    
    # Esperar y subir datos procesados por Hadoop/Pig
    data_folder_path = '/app/shared-data/data'
    print(f"\nEsperando datos procesados en: {data_folder_path}")
    
    # Sistema de reintentos para esperar que termine el processing
    max_intentos = 100
    for intento in range(max_intentos):
        try:
            if os.path.exists(data_folder_path):
                archivos = os.listdir(data_folder_path)
                if archivos:
                    print(f"Encontrados {len(archivos)} archivos procesados")
                    if subir_datasets_a_elasticsearch(data_folder_path):
                        print("Carga completada exitosamente")
                    break
            
            # Continuar esperando si no hay archivos aún
            if intento < max_intentos - 1:
                print(f"Esperando... (intento {intento + 1}/{max_intentos})")
                import time
                time.sleep(10)
        except Exception as e:
            print(f"Error en intento {intento + 1}: {e}")
    
    # Verificaciones finales de conexión
    IntentoConexion()
    
    # Crear Data Views automáticamente en Kibana
    crear_data_views_kibana()
    
    # Realizar consultas estáticas y enviar resultados a caché
    realizar_consultas_estaticas()
    
    print("Carga de datos completada exitosamente")
    print("El contenedor elastic terminará - Elasticsearch y Kibana siguen disponibles")
    


if __name__ == "__main__":
    main()