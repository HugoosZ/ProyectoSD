#!/bin/bash

echo "🔍 TESTING DE CONSULTAS ESTÁTICAS Y CACHÉ"
echo "=" | tr -c '\n' '=' | head -c 50 && echo

echo "=== VERIFICACIÓN DEL CACHÉ ==="
echo

# Verificar que el API de caché está funcionando
echo "--- Estado del servicio de caché ---"
curl -s http://localhost:8000/health | jq .
echo

# Verificar consultas guardadas en caché
echo "--- Consultas guardadas en caché ---"

consultas=(
    "total_de_eventos_por_tipo"
    "eventos_por_comuna_(top_10)"
    "distribución_por_subtipo" 
    "eventos_en_las_últimas_24_horas"
    "promedio_de_eventos_por_día"
)

for consulta in "${consultas[@]}"; do
    echo "🔍 Verificando: $consulta"
    key="consulta_estatica:$consulta"
    
    response=$(curl -s "http://localhost:8000/get/$key")
    found=$(echo "$response" | jq -r '.found')
    
    if [ "$found" = "true" ]; then
        total_docs=$(echo "$response" | jq -r '.value' | jq -r '.total_documentos')
        timestamp=$(echo "$response" | jq -r '.value' | jq -r '.timestamp')
        echo "  ✅ Encontrada: $total_docs documentos (timestamp: $timestamp)"
    else
        echo "  ❌ No encontrada en caché"
    fi
    echo
done

echo "=== VERIFICACIÓN DE ELASTICSEARCH ==="
echo

# Verificar índices de Waze
echo "--- Índices de Waze disponibles ---"
curl -s "http://localhost:9200/_cat/indices/waze*?v&s=index" 2>/dev/null || echo "❌ No se pudo conectar a Elasticsearch"
echo

# Verificar conteo de documentos
echo "--- Conteo de documentos por índice ---"
for index in "waze_no-processing-data" "waze_data-unique"; do
    echo "📊 Verificando índice: $index"
    count=$(curl -s "http://localhost:9200/$index/_count" 2>/dev/null | jq -r '.count' 2>/dev/null)
    if [ "$count" != "null" ] && [ "$count" != "" ]; then
        echo "  📋 $index: $count documentos"
    else
        echo "  ❌ Error al consultar $index"
    fi
done
echo

echo "=== PRUEBA DE CONSULTA PERSONALIZADA ==="
echo

# Hacer una consulta personalizada a datos únicos
echo "--- Top 5 tipos de eventos en datos únicos ---"
query='{
  "size": 0,
  "aggs": {
    "tipos": {
      "terms": {
        "field": "tipo",
        "size": 5
      }
    }
  }
}'

result=$(curl -s -X POST "http://localhost:9200/waze_data-unique/_search" \
  -H "Content-Type: application/json" \
  -d "$query" 2>/dev/null)

if [ $? -eq 0 ]; then
    total=$(echo "$result" | jq -r '.hits.total.value')
    echo "📊 Total documentos consultados: $total"
    echo "🏆 Top tipos de eventos:"
    echo "$result" | jq -r '.aggregations.tipos.buckets[] | "  • \(.key): \(.doc_count) eventos"' 2>/dev/null
else
    echo "❌ Error en consulta personalizada"
fi
echo

echo "=== PRUEBA MANUAL DE CACHÉ ==="
echo

# Probar escritura manual en caché
echo "--- Escribiendo dato de prueba en caché ---"
test_payload='{
  "key": "test_manual_bash",
  "value": "{\"mensaje\": \"Prueba desde bash\", \"timestamp\": \"2025-07-01T00:00:00\"}",
  "ttl": 300
}'

write_result=$(curl -s -X POST "http://localhost:8000/set" \
  -H "Content-Type: application/json" \
  -d "$test_payload")

if echo "$write_result" | jq -e '.success' >/dev/null 2>&1; then
    echo "✅ Escritura exitosa"
    
    # Verificar lectura
    echo "--- Leyendo dato de prueba del caché ---"
    read_result=$(curl -s "http://localhost:8000/get/test_manual_bash")
    found=$(echo "$read_result" | jq -r '.found')
    
    if [ "$found" = "true" ]; then
        mensaje=$(echo "$read_result" | jq -r '.value' | jq -r '.mensaje')
        echo "✅ Lectura exitosa: $mensaje"
    else
        echo "❌ No se pudo leer el dato"
    fi
else
    echo "❌ Error en escritura: $write_result"
fi

echo
echo "✅ PRUEBAS COMPLETADAS"
