-- Eliminar duplicados

-- Cargar datos filtrados
raw = LOAD '/processing/filtered_events' USING PigStorage(',') 
    AS (tipo:chararray, subtipo:chararray, ubicacion:chararray, ciudad:chararray, hora:chararray, lat:float, lon:float);

-- Extraer minutos para agrupación por tiempo
raw_with_modified_time = FOREACH raw GENERATE
    tipo,
    subtipo,
    ubicacion,
    ciudad,
    hora,
    REGEX_EXTRACT(hora, '(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}).*', 1) AS hora_reducida,
    lat,
    lon;

-- Agrupar por atributos clave
grouped_events = GROUP raw_with_modified_time BY (tipo, ciudad, hora_reducida, ubicacion);

-- Tomar un evento por grupo
data_unique = FOREACH grouped_events {
    first = LIMIT raw_with_modified_time 1;
    GENERATE FLATTEN(first.(tipo, subtipo, ubicacion, ciudad, hora, lat, lon));
};

-- Guardar resultado
STORE data_unique INTO '/processing/data_unique' USING PigStorage(',');
