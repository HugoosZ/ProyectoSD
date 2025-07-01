#!/usr/bin/env python3
"""
Script para probar las consultas estáticas a Elasticsearch y el caché
"""

import requests
import json
from elasticsearch import Elasticsearch

def test_elasticsearch_consultas():
    """Prueba las consultas estáticas directamente en Elasticsearch"""
    try:
        es = Elasticsearch("http://localhost:9200")
        if not es.ping():
            print("❌ Elasticsearch no disponible")
            return
            
        print("✅ Elasticsearch conectado")
        print("\n=== PRUEBAS DE CONSULTAS DIRECTAS ===")
        
        # Consulta personalizada: Eventos por tipo en datos únicos
        consulta_tipos = {
            "size": 0,
            "aggs": {
                "tipos": {
                    "terms": {
                        "field": "tipo",
                        "size": 20
                    }
                }
            }
        }
        
        print("\n--- Tipos de eventos en datos únicos ---")
        resultado = es.search(index="waze_data-unique", body=consulta_tipos)
        total = resultado['hits']['total']['value']
        print(f"📊 Total documentos: {total}")
        
        if 'aggregations' in resultado:
            buckets = resultado['aggregations']['tipos']['buckets']
            for bucket in buckets:
                print(f"  • {bucket['key']}: {bucket['doc_count']} eventos")
        
        # Consulta personalizada: Eventos por comuna con filtro
        consulta_comuna_filtrada = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"tipo": "JAM"}}
                    ]
                }
            },
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
        
        print("\n--- Comunas con más atascos (JAM) ---")
        resultado_jam = es.search(index="waze_data-unique", body=consulta_comuna_filtrada)
        total_jam = resultado_jam['hits']['total']['value']
        print(f"📊 Total atascos: {total_jam}")
        
        if 'aggregations' in resultado_jam:
            buckets = resultado_jam['aggregations']['comunas']['buckets']
            for bucket in buckets:
                print(f"  • {bucket['key']}: {bucket['doc_count']} atascos")
                
    except Exception as e:
        print(f"❌ Error en consultas Elasticsearch: {e}")

def test_cache_api():
    """Prueba el API del caché"""
    try:
        cache_url = "http://localhost:8000"
        
        # Test de salud
        response = requests.get(f"{cache_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API de caché disponible")
        else:
            print("❌ API de caché no disponible")
            return
            
        print("\n=== PRUEBAS DEL CACHÉ ===")
        
        # Listar todas las consultas guardadas
        consultas_esperadas = [
            "total_de_eventos_por_tipo",
            "eventos_por_comuna_(top_10)",
            "distribución_por_subtipo",
            "eventos_en_las_últimas_24_horas",
            "promedio_de_eventos_por_día"
        ]
        
        print("\n--- Consultas guardadas en caché ---")
        for consulta in consultas_esperadas:
            cache_key = f"consulta_estatica:{consulta.lower().replace(' ', '_')}"
            response = requests.get(f"{cache_url}/get/{cache_key}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('found'):
                    valor = json.loads(data['value'])
                    print(f"✅ {consulta}: {valor['total_documentos']} docs (timestamp: {valor['timestamp']})")
                else:
                    print(f"❌ {consulta}: No encontrada")
            else:
                print(f"❌ {consulta}: Error en API")
                
        # Test de escritura manual en caché
        print("\n--- Test de escritura manual ---")
        test_data = {
            "key": "test_manual",
            "value": json.dumps({
                "consulta": "Test manual",
                "timestamp": "2025-07-01T00:00:00",
                "resultado": "Prueba exitosa"
            }),
            "ttl": 300  # 5 minutos
        }
        
        response = requests.post(f"{cache_url}/set", json=test_data, timeout=5)
        if response.status_code == 200:
            print("✅ Escritura manual exitosa")
            
            # Verificar lectura
            response = requests.get(f"{cache_url}/get/test_manual", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('found'):
                    print("✅ Lectura manual exitosa")
                else:
                    print("❌ No se pudo leer el dato manual")
        else:
            print("❌ Error en escritura manual")
            
    except Exception as e:
        print(f"❌ Error en pruebas de caché: {e}")

def comparar_datasets():
    """Compara los datasets procesados vs no procesados"""
    try:
        es = Elasticsearch("http://localhost:9200")
        if not es.ping():
            print("❌ Elasticsearch no disponible")
            return
            
        print("\n=== COMPARACIÓN DE DATASETS ===")
        
        # Contar documentos totales
        count_raw = es.count(index="waze_no-processing-data")['count']
        count_unique = es.count(index="waze_data-unique")['count']
        
        print(f"📊 Datos sin procesar: {count_raw:,} documentos")
        print(f"🔹 Datos únicos procesados: {count_unique:,} documentos")
        
        if count_raw > 0:
            reduccion = ((count_raw - count_unique) / count_raw) * 100
            print(f"📈 Reducción por deduplicación: {reduccion:.1f}%")
        
        # Consulta de validación: verificar tipos únicos
        consulta_tipos_raw = {
            "size": 0,
            "aggs": {
                "tipos_unicos": {
                    "cardinality": {
                        "field": "tipo"
                    }
                }
            }
        }
        
        tipos_raw = es.search(index="waze_no-processing-data", body=consulta_tipos_raw)
        tipos_unique = es.search(index="waze_data-unique", body=consulta_tipos_raw)
        
        count_tipos_raw = tipos_raw['aggregations']['tipos_unicos']['value']
        count_tipos_unique = tipos_unique['aggregations']['tipos_unicos']['value']
        
        print(f"\n📋 Tipos únicos en datos sin procesar: {count_tipos_raw}")
        print(f"📋 Tipos únicos en datos procesados: {count_tipos_unique}")
        
    except Exception as e:
        print(f"❌ Error en comparación: {e}")

if __name__ == "__main__":
    print("🔍 TESTING DE CONSULTAS ESTÁTICAS Y CACHÉ")
    print("=" * 50)
    
    test_elasticsearch_consultas()
    test_cache_api()
    comparar_datasets()
    
    print("\n✅ Pruebas completadas")
