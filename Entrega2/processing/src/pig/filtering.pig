-- Limpieza de datos

-- Cargar CSV
raw = LOAD '/processing/data_for_pig.csv' USING PigStorage(',') 
    AS (tipo:chararray, subtipo:chararray, ubicacion:chararray, ciudad:chararray, hora:chararray, lat:float, lon:float);

-- Filtrar registros inválidos
filtered_events = FILTER raw BY 
    tipo IS NOT NULL AND 
    hora IS NOT NULL AND 
    hora MATCHES '\\d{4}-\\d{2}-\\d{2}.*' AND
    lat IS NOT NULL AND 
    lon IS NOT NULL;

-- Estandarizar tipos
standardized_events = FOREACH filtered_events GENERATE
    (tipo MATCHES 'HAZARD.*' ? 'HAZARD' : tipo) AS tipo,
    subtipo,
    ubicacion,
    UPPER(ciudad) AS ciudad,
    hora,
    lat,
    lon;

-- Guardar datos filtrados
STORE standardized_events INTO '/processing/filtered_events' USING PigStorage(',');