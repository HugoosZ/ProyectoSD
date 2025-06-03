-- Limpieza, normalización y agrupación de incidentes

-- Registrar librería para JSON
REGISTER /usr/lib/pig/piggybank.jar;

-- Cargar datos desde HDFS
raw = LOAD '/processing/data_for_pig.json' 
    USING org.apache.pig.piggybank.storage.JsonLoader(
        'tipo:chararray, 
         subtipo:chararray, 
         ubicacion:chararray, 
         ciudad:chararray, 
         hora:chararray, 
         lat:float, 
         lon:float'
    );

-- Filtrar datos inválidos
filtered_events = FILTER raw_events BY
    ciudad IS NOT NULL AND
    tipo IS NOT NULL AND
    hora IS NOT NULL AND
    lat IS NOT NULL AND
    lon IS NOT NULL;

-- Estandarizar tipos de incidentes
standardized_events = FOREACH filtered_events GENERATE
    (tipo MATCHES 'HAZARD.*' ? 'HAZARD' : tipo) AS tipo,
    subtipo,
    ubicacion,
    UPPER(ciudad) AS ciudad,
    hora,
    lat,
    lon;

-- Eliminar duplicados
grouped_events = GROUP standardized_events BY 
    (tipo, ciudad, SUBSTRING(hora, 0, 13), ROUND(lat*100)/100, ROUND(lon*100)/100);

clean_events = FOREACH grouped_events {
    first = LIMIT standardized_events 1;
    GENERATE FLATTEN(first);
};

-- Guardar datos limpios
STORE clean_events INTO '/processing/cleaned_grouped_events' USING PigStorage(',');