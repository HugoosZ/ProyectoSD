-- Limpieza, normalización y agrupación de incidentes

-- Cargar datos desde HDFS
raw = LOAD '/processing/data_for_pig.json' 
    USING JsonLoader('tipo:chararray,subtipo:chararray,ubicacion:chararray,ciudad:chararray,hora:chararray,lat:double,lon:double');

-- Filtrar registros inválidos
valid = FILTER raw BY 
    tipo IS NOT NULL AND tipo != '' AND
    ubicacion IS NOT NULL AND ubicacion != '' AND
    ciudad IS NOT NULL AND ciudad != '' AND
    hora IS NOT NULL AND hora != '' AND
    lat IS NOT NULL AND lon IS NOT NULL;

-- Normalizar strings
norm = FOREACH valid GENERATE 
    LOWER(TRIM(tipo)) AS tipo,
    LOWER(TRIM(subtipo)) AS subtipo,
    TRIM(ubicacion) AS ubicacion,
    TRIM(ciudad) AS ciudad,
    hora AS hora,
    lat AS lat,
    lon AS lon;

-- Eliminar duplicados
unique = DISTINCT norm;

-- Redondear lat/lon a 3 decimales (≈100m de precisión)
normalized_coords = FOREACH unique GENERATE
    tipo, subtipo, ubicacion, ciudad, hora,
    ROUND(lat * 1000) / 1000.0 AS lat_round,
    ROUND(lon * 1000) / 1000.0 AS lon_round,
    lat, lon;

-- Agrupar por tipo, ciudad y coordenadas redondeadas
grouped = GROUP normalized_coords BY (tipo, ciudad, lat_round, lon_round);

-- Obtener el incidente más reciente por grupo
result = FOREACH grouped {
    sorted = ORDER normalized_coords BY hora DESC;
    top = LIMIT sorted 1;
    GENERATE 
        FLATTEN(top.tipo) AS tipo,
        FLATTEN(top.subtipo) AS subtipo,
        FLATTEN(top.ubicacion) AS ubicacion,
        FLATTEN(top.ciudad) AS ciudad,
        FLATTEN(top.hora) AS hora,
        FLATTEN(top.lat) AS lat,
        FLATTEN(top.lon) AS lon;
}

-- Guardar resultados
STORE result INTO '/processing/cleaned_grouped_events' USING PigStorage(',');
