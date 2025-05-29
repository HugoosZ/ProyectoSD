#!/bin/bash

echo "⏳ Esperando a que el NameNode salga del Safe Mode..."

while hdfs dfsadmin -safemode get | grep -q "ON"; do
  echo "🔒 Safe Mode aún activo. Esperando 5 segundos..."
  sleep 5
done

echo "✅ NameNode fuera de Safe Mode. Continuando..."