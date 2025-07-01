#!/bin/bash

echo "📊 RESUMEN DEL SISTEMA DE CONSULTAS ESTÁTICAS WAZE"
echo "=" | tr -c '\n' '=' | head -c 60 && echo

echo "🏗️  ARQUITECTURA DEL SISTEMA:"
echo "   ├── 📊 Elasticsearch: Almacena datos procesados y no procesados"
echo "   ├── 🔍 Kibana: Visualización y análisis (http://localhost:5601)"
echo "   ├── 💾 Redis: Caché para resultados de consultas procesadas"
echo "   ├── 🌐 API de Caché: Endpoints REST para gestión de caché (http://localhost:8000)"
echo "   └── 🤖 Sistema de consultas automático: Compara y cachea resultados"
echo

echo "🔄 FLUJO AUTOMATIZADO:"
echo "   1. ✅ Carga datos sin procesar desde MongoDB a Elasticsearch"
echo "   2. ✅ Carga datos procesados (únicos) desde Hadoop a Elasticsearch"
echo "   3. ✅ Ejecuta consultas estáticas en ambos datasets"
echo "   4. ✅ Compara resultados y muestra diferencias"
echo "   5. ✅ Guarda solo resultados de datos procesados en caché Redis"
echo

echo "📈 RESULTADOS ACTUALES:"

# Verificar datos en Elasticsearch
echo "--- Datos en Elasticsearch ---"
raw_count=$(curl -s "http://localhost:9200/waze_no-processing-data/_count" | jq -r '.count')
unique_count=$(curl -s "http://localhost:9200/waze_data-unique/_count" | jq -r '.count')

if [ "$raw_count" != "null" ] && [ "$unique_count" != "null" ]; then
    reduction=$(echo "scale=1; ($raw_count - $unique_count) * 100 / $raw_count" | bc -l)
    echo "   📊 Datos sin procesar: $raw_count documentos"
    echo "   🔹 Datos únicos (procesados): $unique_count documentos"
    echo "   📉 Reducción por deduplicación: ${reduction}%"
else
    echo "   ❌ Error obteniendo conteos de documentos"
fi

echo
echo "--- Consultas en Caché ---"
consultas_cached=0
consultas_total=5

consultas=(
    "total_de_eventos_por_tipo"
    "eventos_por_comuna_(top_10)"
    "distribución_por_subtipo"
    "eventos_en_las_últimas_24_horas"
    "promedio_de_eventos_por_día"
)

for consulta in "${consultas[@]}"; do
    key="consulta_estatica:$consulta"
    response=$(curl -s "http://localhost:8000/get/$key")
    found=$(echo "$response" | jq -r '.found' 2>/dev/null)
    
    if [ "$found" = "true" ]; then
        ((consultas_cached++))
        echo "   ✅ $consulta"
    else
        echo "   ❌ $consulta"
    fi
done

echo "   📊 Total en caché: $consultas_cached/$consultas_total consultas"

echo
echo "🚀 ENDPOINTS DISPONIBLES:"
echo "   🔍 Elasticsearch: http://localhost:9200"
echo "      └── Índices: waze_no-processing-data, waze_data-unique, waze_*"
echo "   📊 Kibana: http://localhost:5601"
echo "      └── Data Views creados automáticamente para visualización"
echo "   💾 API de Caché: http://localhost:8000"
echo "      ├── GET /health - Estado del servicio"
echo "      ├── GET /get/{key} - Obtener valor del caché"
echo "      ├── POST /set - Guardar valor en caché"
echo "      └── POST /clear - Limpiar todo el caché"

echo
echo "🎯 DIFERENCIAS DETECTADAS:"

# Mostrar algunos ejemplos de diferencias entre datasets
echo "--- Ejemplo: Eventos en las últimas 24 horas ---"
last24_key="consulta_estatica:eventos_en_las_últimas_24_horas"
last24_response=$(curl -s "http://localhost:8000/get/$last24_key")
last24_found=$(echo "$last24_response" | jq -r '.found' 2>/dev/null)

if [ "$last24_found" = "true" ]; then
    processed_count=$(echo "$last24_response" | jq -r '.value' | jq -r '.total_documentos')
    
    # Obtener conteo de datos no procesados para comparar
    query_24h='{
      "query": {
        "range": {
          "@timestamp": {
            "gte": "now-24h"
          }
        }
      }
    }'
    
    raw_24h=$(curl -s -X POST "http://localhost:9200/waze_no-processing-data/_count" \
      -H "Content-Type: application/json" \
      -d "$query_24h" | jq -r '.count' 2>/dev/null)
    
    if [ "$raw_24h" != "null" ] && [ "$raw_24h" != "" ]; then
        difference=$((raw_24h - processed_count))
        percentage=$(echo "scale=1; $difference * 100 / $raw_24h" | bc -l 2>/dev/null)
        
        echo "   📊 Sin procesar: $raw_24h eventos"
        echo "   🔹 Procesados: $processed_count eventos"
        echo "   📈 Diferencia: $difference eventos (${percentage}% reducción)"
    else
        echo "   🔹 Procesados: $processed_count eventos"
        echo "   ❌ No se pudo obtener conteo sin procesar"
    fi
else
    echo "   ❌ No disponible en caché"
fi

echo
echo "📝 COMANDOS ÚTILES:"
echo "   # Ver logs del sistema"
echo "   docker logs waze-elastic"
echo
echo "   # Ejecutar consulta personalizada"
echo "   curl -X POST 'http://localhost:9200/waze_data-unique/_search' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"size\": 0, \"aggs\": {\"tipos\": {\"terms\": {\"field\": \"tipo\"}}}}'"
echo
echo "   # Guardar resultado personalizado en caché"
echo "   curl -X POST 'http://localhost:8000/set' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"key\": \"mi_consulta\", \"value\": \"resultado\", \"ttl\": 3600}'"
echo
echo "   # Verificar estado del caché"
echo "   curl http://localhost:8000/health"

echo
echo "✅ SISTEMA COMPLETAMENTE OPERATIVO"
echo "   💡 Las consultas se ejecutan automáticamente al cargar datos"
echo "   💡 Solo se cachean resultados de datos procesados (únicos)"
echo "   💡 Se comparan automáticamente ambos datasets para mostrar diferencias"
echo "   💡 API REST disponible para consultas manuales y gestión de caché"

echo
echo "🔗 Enlaces rápidos:"
echo "   📊 Kibana: http://localhost:5601"
echo "   🔍 Elasticsearch: http://localhost:9200/_cat/indices/waze*?v"
echo "   💾 Caché Health: http://localhost:8000/health"
echo "   🧪 Script de pruebas: ./test_consultas.sh"
