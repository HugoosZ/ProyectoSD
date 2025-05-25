-- Cargar datos limpios desde HDFS
clean_data = LOAD '/data/data_for_pig.json' USING JsonLoader('tipo:chararray, ubicacion:chararray, hora:long');

-- Filtrar por tipo de incidente
accidentes = FILTER clean_data BY tipo == 'ACCIDENT';

-- Agrupar por ubicación
grouped = GROUP accidentes BY ubicacion;

-- Contar incidentes por ubicación
incident_counts = FOREACH grouped GENERATE group AS location, COUNT(accidentes) AS total_incidents;

-- Almacenar resultados
STORE incident_counts INTO '/output/incident_counts' USING PigStorage(',');