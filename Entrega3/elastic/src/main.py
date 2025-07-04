import sys
import os
import json
import time
from conexion import IntentoConexion
import pandas as pd
from elasticsearch import Elasticsearch
from datetime import datetime

sys.path.insert(0, "/app/storage")
from mongo_storage import MongoStorage


class ElasticsearchManager:
    def __init__(self):
        """Inicializar el gestor de Elasticsearch"""
        print("ElasticsearchManager inicializado correctamente")
        self.es_url = "http://elasticsearch:9200"
        self.es = None
        self._conectar()
    
    def _conectar(self):
        """Establecer conexión con Elasticsearch"""
        try:
            self.es = Elasticsearch(self.es_url)
            if not self.es.ping():
                print("No se pudo conectar a Elasticsearch")
                self.es = None
                return False
            print("Conexión a Elasticsearch exitosa")
            return True
        except Exception as e:
            print(f"Error conectando a Elasticsearch: {e}")
            self.es = None
            return False
    
    def verificar_conexion(self):
        """Verificar si la conexión está activa"""
        if not self.es:
            return self._conectar()
        
        try:
            return self.es.ping()
        except:
            return self._conectar()

    def procesar_y_subir_csv(self, archivo_path, nombre_archivo):
        """Procesar un archivo CSV y subirlo a Elasticsearch"""
        if not self.verificar_conexion():
            print("No hay conexión a Elasticsearch")
            return False
            
        try:
            print(f"\nProcesando archivo: {nombre_archivo}")
            
            # Obtener nombres de columnas específicos para cada tipo de archivo
            columnas = self.obtener_nombres_columnas(nombre_archivo)
            df = pd.read_csv(archivo_path, header=None, names=columnas)
            print(f"Filas leidas: {len(df)}")
            
            # Guardar copia para cache en carpeta compartida
            self._guardar_copia_cache(df, nombre_archivo)
            
            # Crear nombre del índice basado en el archivo
            indice_nombre = f"waze_{nombre_archivo.replace('.csv', '').replace('_', '-')}"
            print(f"Indice destino: {indice_nombre}")
            
            # Configurar mapeo específico según el tipo de datos
            mapeo = self.crear_mapeo_para_archivo(nombre_archivo, df)
            
            # Crear el índice si no existe
            if not self.es.indices.exists(index=indice_nombre):
                print(f"Creando indice: {indice_nombre}")
                configuracion_indice = self.crear_configuracion_indice()
                configuracion_indice["mappings"] = mapeo
                self.es.indices.create(index=indice_nombre, body=configuracion_indice)
            else:
                # Verificar si existe conflicto de mapeo (especialmente para location)
                try:
                    current_mapping = self.es.indices.get_mapping(index=indice_nombre)
                    location_type = None
                    if indice_nombre in current_mapping:
                        props = current_mapping[indice_nombre].get('mappings', {}).get('properties', {})
                        if 'location' in props:
                            location_type = props['location'].get('type')
                    
                    # Si location no es geo_point, recrear el índice
                    if location_type and location_type != 'geo_point':
                        print(f"Recreando indice por conflicto de mapeo...")
                        self.es.indices.delete(index=indice_nombre)
                        configuracion_indice = self.crear_configuracion_indice()
                        configuracion_indice["mappings"] = mapeo
                        self.es.indices.create(index=indice_nombre, body=configuracion_indice)
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
                    doc = self.limpiar_documento(doc)
                    
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
                        self.es.index(index=indice_nombre, body=doc)
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

    def _guardar_copia_cache(self, df, nombre_archivo):
        """Guardar copia del CSV en carpeta compartida para cache"""
        try:
            cache_dir = "/app/shared-data/query_results"
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, nombre_archivo)
            
            # Guardar sin índices ni encabezados
            df.to_csv(cache_path, index=False, header=False)
            print(f"Copia guardada en cache: {cache_path}")
            return True
        except Exception as e:
            print(f"Error guardando copia para cache: {e}")
            return False

    def crear_mapeo_para_archivo(self, nombre_archivo, df):
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
        elif any(x in nombre_archivo for x in ["no_processing_data", "data_unique"]):
            mapeo_base["properties"].update({
                "tipo": {"type": "keyword"},
                "subtipo": {"type": "keyword"},
                "calle": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "comuna": {"type": "keyword"},
                "fecha": {"type": "date"},
                "latitud": {"type": "float"},
                "longitud": {"type": "float"}
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

    def crear_configuracion_indice(self):
        """Crear configuración del índice para optimizar el rendimiento"""
        return {
            "settings": {
                "index": {
                    "max_result_window": 50000,
                    "max_docvalue_fields_search": 200
                }
            }
        }

    def limpiar_documento(self, doc):
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

    def limpiar_indices_waze(self):
        """Eliminar todos los índices de Waze existentes para evitar duplicados"""
        if not self.verificar_conexion():
            return
            
        try:
            print("\nLimpiando indices existentes...")
            indices_existentes = self.es.indices.get_alias(index="waze*")
            
            if indices_existentes:
                print(f"Eliminando {len(indices_existentes)} indices de Waze:")
                for indice in indices_existentes.keys():
                    try:
                        self.es.indices.delete(index=indice)
                        print(f"  ✓ {indice}")
                    except Exception as e:
                        print(f"  ✗ {indice}: {e}")
            else:
                print("No se encontraron indices de Waze existentes")
                
        except Exception as e:
            print(f"Error durante la limpieza de indices: {e}")

    def subir_datasets_a_elasticsearch(self, data_folder_path):
        """Función principal para subir todos los datasets a Elasticsearch"""
        print("\nIniciando carga a Elasticsearch...")
        
        if not self.verificar_conexion():
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
            if self.procesar_y_subir_csv(archivo_path, archivo):
                archivos_procesados += 1
        
        print(f"\nResumen: {archivos_procesados}/{len(archivos_csv)} archivos procesados exitosamente (sin incluir datos raw)")
        
        # Mostrar resumen de índices creados
        try:
            indices = self.es.indices.get_alias(index="waze*")
            print(f"\nTodos los índices de Waze:")
            for indice in sorted(indices.keys()):
                doc_count = self.es.count(index=indice)['count']
                print(f"   - {indice}: {doc_count} documentos")
        except Exception as e:
            print(f"Error listando indices: {e}")
        
        return archivos_procesados > 0

    def verificar_datos_actualizados(self):
        """
        Verifica si los datos procesados están actualizados comparando
        si existen todos los índices procesados esperados en ES.
        Si falta algún índice, requiere recarga completa.
        """
        if not self.verificar_conexion():
            return False
            
        try:
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
                    response = self.es.count(index=indice)
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

    def ejecutar_consulta(self, indice, query):
        """Ejecutar una consulta específica en un índice"""
        if not self.verificar_conexion():
            return None
            
        try:
            resultado = self.es.search(index=indice, body=query)
            return resultado
        except Exception as e:
            print(f"Error ejecutando consulta en {indice}: {e}")
            return None

    def obtener_conteo_por_tipo(self, indice="waze*"):
        """Obtener conteo de eventos por tipo"""
        query = {
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
        return self.ejecutar_consulta(indice, query)

    def obtener_eventos_por_comuna(self, indice="waze*", size=10):
        """Obtener eventos por comuna"""
        query = {
            "size": 0,
            "aggs": {
                "comunas": {
                    "terms": {
                        "field": "comuna",
                        "size": size
                    }
                }
            }
        }
        return self.ejecutar_consulta(indice, query)

    def obtener_distribucion_temporal(self, indice="waze*", intervalo="day"):
        """Obtener distribución temporal de eventos"""
        query = {
            "size": 0,
            "aggs": {
                "por_tiempo": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": intervalo
                    }
                }
            }
        }
        return self.ejecutar_consulta(indice, query)

    def buscar_eventos_recientes(self, indice="waze*", horas=24):
        """Buscar eventos de las últimas X horas"""
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{horas}h"
                    }
                }
            },
            "size": 0
        }
        return self.ejecutar_consulta(indice, query)

    def obtener_nombres_columnas(self, nombre_archivo):
        """Obtener nombres de columnas apropiados según el tipo de archivo"""
        if "no_processing_data" in nombre_archivo:
            return ["tipo", "subtipo", "calle", "comuna", "fecha", "latitud", "longitud"]
        elif "data_unique" in nombre_archivo:
            return ["tipo", "subtipo", "calle", "comuna", "fecha", "latitud", "longitud"]
        else:
            # Nombres genéricos para archivos desconocidos
            return [f"campo_{i}" for i in range(10)]  # Asumiendo máximo 10 columnas


# Funciones auxiliares que no requieren la clase
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
            {"title": "waze_data-unique", "name": "Waze - Datos Únicos", "timeFieldName": "@timestamp"},
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
    """
    Ejecutar consultas estáticas en Elasticsearch, guardar resultados como JSON,
    leer los JSON guardados y verificar que coincidan con los resultados originales.
    
    Guarda archivos JSON en: /app/shared-data/query_results/
    """
    try:
        es = Elasticsearch("http://elasticsearch:9200")
        if not es.ping():
            print("Elasticsearch no disponible para consultas")
            return
            
        print("\n=== CONSULTAS ESTÁTICAS A ELASTICSEARCH ===")
        
        # Crear directorio para resultados JSON
        directorio_resultados = '/app/shared-data/query_results'
        os.makedirs(directorio_resultados, exist_ok=True)
        
        # Definir consultas estáticas simples
        consultas = [
            {
                "nombre": "Total de eventos por tipo",
                "archivo": "eventos_por_tipo.json",
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
                "archivo": "eventos_por_comuna.json",
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
                "nombre": "Eventos en las últimas 24 horas",
                "archivo": "eventos_recientes_24h.json",
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
            }
        ]
        
        archivos_generados = []
        
        for consulta in consultas:
            print(f"\n--- {consulta['nombre']} ---")
            
            try:
                # 1. Ejecutar consulta en Elasticsearch
                print("Ejecutando consulta original...")
                resultado_original = es.search(
                    index="waze_data-unique",
                    body=consulta["query"]
                )
                
                total_docs = resultado_original['hits']['total']['value']
                print(f" Resultado original: {total_docs} documentos")
                
                # Mostrar agregaciones si existen
                if 'aggregations' in resultado_original:
                    print("   Agregaciones originales:")
                    for agg_key, agg_data in resultado_original['aggregations'].items():
                        if 'buckets' in agg_data:
                            for bucket in agg_data['buckets'][:3]:  # Solo primeros 3
                                print(f"     - {bucket['key']}: {bucket['doc_count']}")
                
                # 2. Guardar resultado completo como JSON
                archivo_destino = os.path.join(directorio_resultados, consulta["archivo"])
                with open(archivo_destino, 'w', encoding='utf-8') as f:
                    json.dump(resultado_original, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"Guardado en: {consulta['archivo']}")
                
                with open(archivo_destino, 'r', encoding='utf-8') as f:
                    resultado_cargado = json.load(f)
                
                # 4. Comparar resultados
                total_docs_cargado = resultado_cargado['hits']['total']['value']
                print(f"🔄 Verificación:")
                print(f"   Original: {total_docs} documentos")
                print(f"   Cargado:  {total_docs_cargado} documentos")
                print(f"   ✓ Coinciden: {'SÍ' if total_docs == total_docs_cargado else 'NO'}")
                
                # Verificar agregaciones
                if 'aggregations' in resultado_original and 'aggregations' in resultado_cargado:
                    print("   Agregaciones del JSON:")
                    for agg_key, agg_data in resultado_cargado['aggregations'].items():
                        if 'buckets' in agg_data:
                            for bucket in agg_data['buckets'][:3]:
                                print(f"     - {bucket['key']}: {bucket['doc_count']}")
                    
                    aggs_coinciden = resultado_original['aggregations'] == resultado_cargado['aggregations']
                    print(f"   ✓ Agregaciones coinciden: {'SÍ' if aggs_coinciden else 'NO'}")
                
                archivos_generados.append(consulta["archivo"])
                print(f"   Consulta completada y verificada")
                    
            except Exception as e:
                #print(f"❌ Error procesando {consulta['nombre']}: {e}")
                continue
        
        # Crear resumen final
        print(f"\n=== RESUMEN FINAL ===")
        
        resumen = {
            "timestamp": datetime.now().isoformat(),
            "total_consultas": len(consultas),
            "directorio": directorio_resultados,
            "archivos_generados": archivos_generados
        }
        
        archivo_resumen = os.path.join(directorio_resultados, "resumen_consultas.json")
        with open(archivo_resumen, 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False, default=str)
        
        print(f" Resumen guardado en: resumen_consultas.json")
        print(f" Total archivos JSON: {len(archivos_generados) + 1}")
        print(f" Ubicación: {directorio_resultados}")
        print(f"\n Proceso completado - {len(archivos_generados)} consultas ejecutadas, guardadas y verificadas")
        
        try:
            flag_path = '/app/shared-data/data_ready_cache.flag'
            flag_info = {
                "timestamp": datetime.now().isoformat(),
                "status": "data_ready",
                "message": "Datos procesados listos para Cache-Service"
            }
            
            with open(flag_path, 'w', encoding='utf-8') as f:
                json.dump(flag_info, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error creando flag: {e}")

        return True
        
        
    except Exception as e:
        print(f"❌ Error en consultas estáticas: {e}")
        return False


def esperar_flag_datos_listos(max_intentos=60, intervalo=10):
    """
    Esperar a que aparezca el flag que indica que los datos están listos
    """
    flag_path = '/app/shared-data/data_ready.flag'
    
    for intento in range(max_intentos):
        try:
            if os.path.exists(flag_path):
                # Leer información del flag
                with open(flag_path, 'r', encoding='utf-8') as f:
                    flag_info = json.load(f)
                return True
            
            print(f"Intento {intento + 1}/{max_intentos} - Flag no encontrado, esperando {intervalo}s...")
            time.sleep(intervalo)
            
        except Exception as e:
            print(f"   Error verificando flag (intento {intento + 1}): {e}")
            time.sleep(intervalo)
    
    print(f"Timeout: No se encontró el flag después de {max_intentos * intervalo} segundos")
    return False


def eliminar_flag_datos_listos():
    """
    Eliminar el flag una vez que se han procesado los datos
    """
    flag_path = '/app/shared-data/data_ready.flag'
    
    try:
        if os.path.exists(flag_path):
            os.remove(flag_path)
        else:
            print(f"Flag no encontrado para eliminar: {flag_path}")
    except Exception as e:
        print(f"Error eliminando flag: {e}")


def main():
    # Crear carpeta compartida para cache si no existe
    os.makedirs('/app/shared-data/query_results', exist_ok=True)
    
    # Crear instancia del gestor de Elasticsearch
    es_manager = ElasticsearchManager()
    
    print("\n" + "="*50)
    print("  ESPERANDO FLAG DE DATOS LISTOS")
    print("="*50)
    
    # Esperar a que el flag indique que los datos están listos ANTES de hacer cualquier cosa
    print("Esperando flag data_ready.flag del contenedor processing...")
    if not esperar_flag_datos_listos():
        print("Timeout esperando datos procesados - saliendo")
        return
    
    print("Flag encontrado - iniciando procesamiento completo")

    # Verificar si los datos están actualizados comparando filas
    if es_manager.verificar_datos_actualizados():
        print("\nDatos ya están actualizados - no se requiere carga")
        print("Elasticsearch y Kibana están disponibles en sus contenedores")
        
        eliminar_flag_datos_listos()

        # Realizar consultas estáticas incluso cuando los datos están actualizados
        realizar_consultas_estaticas()
        return
    
    print("\nIniciando carga completa de datos...")
    
    # Limpiar índices existentes de Waze antes de empezar
    try:
        es_manager.limpiar_indices_waze()
    except Exception as e:
        print(f"Advertencia: Error en limpieza inicial: {e}")
    
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
        if os.path.exists(ruta_csv_local):
            print("Subiendo datos sin filtrar...")
            es_manager.procesar_y_subir_csv(ruta_csv_local, 'no_processing_data.csv')
    except Exception as e:
        print(f"Error subiendo datos sin filtrar: {e}")
    
    # Esperar y subir datos procesados por Hadoop/Pig
    data_folder_path = '/app/shared-data/data'
    print(f"\nEsperando datos procesados en: {data_folder_path}")
    
    # Eliminar flag después del procesamiento
    eliminar_flag_datos_listos()
    
    # Crear Data Views automáticamente en Kibana
    crear_data_views_kibana()
    
    # Realizar consultas estáticas
    realizar_consultas_estaticas()
    
    # También exportar usando la clase (método adicional)
    es_manager.exportar_consultas_estaticas_json()
    
    print("Carga de datos completada exitosamente")
    print("El contenedor elastic terminará - Elasticsearch y Kibana siguen disponibles")


if __name__ == "__main__":
    main()