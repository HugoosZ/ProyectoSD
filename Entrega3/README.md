# ProyectoSD - Entrega 3

## Descripción

Se implementa un sistema distribuido completo que integra múltiples tecnologías para el procesamiento, análisis y visualización de datos de tráfico de Waze. El sistema utiliza Apache Pig y Hadoop para el procesamiento de datos, Elasticsearch para búsquedas y análisis avanzados, Kibana para visualización de datos, Redis para cache inteligente, y MongoDB para almacenamiento persistente. Los servicios se orquestan mediante Docker Compose con un sistema de flags para coordinar la comunicación entre componentes.

## Arquitectura del Sistema

El sistema está compuesto por los siguientes servicios:

### Servicios Principales
- **MongoDB (storage)**: Base de datos para almacenamiento persistente de datos de tráfico
- **Hadoop (namenode + datanode)**: Cluster para procesamiento distribuido de big data
- **Elasticsearch**: Motor de búsqueda y análisis de datos en tiempo real
- **Kibana**: Interfaz web para visualización y análisis de datos
- **Redis**: Cache inteligente con política LFU (Least Frequently Used)

### Servicios de Procesamiento
- **Scraper**: Recolección de datos de tráfico de Waze
- **Processing**: Procesamiento de datos usando Apache Pig en Hadoop
- **Elastic**: Carga e indexación de datos en Elasticsearch
- **Cache Service**: Gestión inteligente de cache con Redis

## Sistema de Flags de Coordinación

El sistema implementa un mecanismo de flags para coordinar la ejecución secuencial de los servicios:

### Flag `data_ready.flag`
- **Propósito**: Indica que el procesamiento de Hadoop/Pig ha finalizado
- **Creado por**: Servicio `waze-processing`
- **Consumido por**: Servicio `waze-elastic`
- **Ubicación**: `/shared-data/data_ready.flag`
- **Contenido**: JSON con metadata del procesamiento

### Flag `data_ready_cache.flag`
- **Propósito**: Indica que los datos están listos para cache
- **Creado por**: Servicio `waze-elastic`
- **Consumido por**: Servicio `waze-cache-service`
- **Ubicación**: `/shared-data/data_ready_cache.flag`
- **Contenido**: JSON con información de los archivos procesados

### Flujo de Flags

```
1. Processing (Hadoop/Pig) → crea data_ready.flag
2. Elastic lee data_ready.flag → procesa datos → crea data_ready_cache.flag
3. Cache Service lee data_ready_cache.flag → carga datos en Redis
```

## Integraciones Adicionales

### Elasticsearch + Kibana

#### Elasticsearch
- **Funcionalidad**: 
  - Indexación automática de datos procesados por Hadoop
  - Almacenamiento de datos sin procesar desde MongoDB
  - Mapeo de datos geoespaciales (geo_point)
  - Creación automática de índices optimizados

#### Kibana
- **Funcionalidad**:
  - Interfaz web para visualización de datos
  - Dashboards interactivos
  - Creación automática de Data Views
  - Análisis geoespacial con mapas

#### Acceso a Kibana
Una vez iniciado el sistema, accede a Kibana en:
```
http://localhost:5601
```

#### Data Views Automáticos
El sistema crea automáticamente los siguientes Data Views en Kibana:
- `waze-no-processing-data`: Datos sin procesar
- `waze-*`: Patrón para todos los índices de datos procesados

### Sistema de Cache con Redis

#### Redis Configuration
- **Política de memoria**: `allkeys-lfu` (Least Frequently Used)

#### Cache Service
- **Funcionalidad**:
  - Carga automática de resultados de consultas en cache
  - Gestión inteligente de memoria con política LFU
  - Monitoreo de disponibilidad de datos
  - Eliminación automática de flags después del procesamiento

## Configuración de Variables de Entorno

Antes de ejecutar el sistema, configura los siguientes archivos:

### mongo.env
```bash
MONGO_URI="mongodb+srv://usuario:contraseña@cluster.mongodb.net/database"
```

### redis.env (ya configurado)
```bash
REDIS_HOST=redis-exp-lfu
REDIS_PORT=6379
```

## Inicialización del Sistema

El sistema se ejecuta de forma secuencial y coordinada usando dependencias y el sistema de flags:

### Orden de Inicialización
1. **MongoDB (storage)** - Base de datos principal
2. **Hadoop (namenode + datanode)** - Cluster de procesamiento
3. **Elasticsearch** - Motor de búsqueda
4. **Kibana** - Interfaz de visualización
5. **Redis** - Servicio de cache
6. **Scraper** - Recolección de datos
7. **Processing** - Procesamiento con Hadoop/Pig
8. **Elastic** - Carga de datos en Elasticsearch
9. **Cache Service** - Carga de datos en Redis

### Flujo de Procesamiento
1. El **scraper** recolecta datos y los almacena en MongoDB
2. **Processing** espera a que Hadoop salga del modo seguro, procesa los datos con Pig y crea `data_ready.flag`
3. **Elastic** detecta la flag, carga datos en Elasticsearch, crea Data Views en Kibana y genera `data_ready_cache.flag`
4. **Cache Service** detecta la flag y carga los resultados en Redis

## Ejecución del Proyecto

Para construir y levantar todos los servicios, ejecuta desde la carpeta `Entrega3/`:

```bash
docker compose up --build
```

### Verificación de Servicios

Una vez iniciado, verifica que los servicios estén funcionando:

```bash
# Verificar estado de contenedores
docker compose ps

# Verificar logs de un servicio específico
docker compose logs [nombre-servicio]

# Ejemplos:
docker compose logs waze-elastic
docker compose logs redis-exp-lfu
docker compose logs kibana
```

## Acceso a los Servicios

### Kibana (Visualización de Datos)
- **URL**: http://localhost:5601
- **Funcionalidades**:
  - Visualización de datos en tiempo real
  - Creación de dashboards personalizados
  - Análisis geoespacial con mapas
  - Exploración de datos con filtros avanzados

### Elasticsearch (API de Búsqueda)
- **URL**: http://localhost:9200


### Redis (Monitoreo del Cache)
```bash
# Conectar al contenedor Redis
docker exec -it redis-exp-lfu redis-cli

# Comandos útiles en Redis
INFO memory          # Información de memoria
KEYS *              # Listar todas las claves
GET <clave>         # Obtener valor de una clave
```

## Volúmenes y Persistencia

### Volúmenes Principales
- `esdata`: Datos de Elasticsearch
- `redis-exp-lfu-data`: Datos persistentes de Redis
- `processing-results`: Resultados del procesamiento de Hadoop
- `shared-data`: Directorio compartido entre servicios para flags y datos

### Directorios Compartidos
- `/shared-data/`: Flags de coordinación y datos compartidos
- `/shared-data/query_results/`: Resultados para cache
- `/shared-data/data/`: Datos procesados
- `/hadoop-data/`: Datos persistentes de Hadoop (namenode y datanode)

---

## Arquitectura de Datos

### Flujo de Datos
```
Waze API → Scraper → MongoDB → Processing (Hadoop/Pig) → 
         ↓
Elasticsearch ← Elastic Service ← data_ready.flag
         ↓
Kibana (Visualización)
         ↓
Redis ← Cache Service ← data_ready_cache.flag
```

### Tipos de Datos Procesados
- **Datos sin procesar**: Eventos directos de Waze almacenados en MongoDB y Elasticsearch
- **Datos agregados**: Estadísticas por hora, tipo de evento, ubicación geográfica
- **Datos en cache**: Consultas frecuentes y resultados pre-calculados en Redis