-- Cargar los datos JSON con el esquema
data = LOAD '/processing/data_for_pig.json' USING JsonLoader('type:chararray,severity:int,timestamp:long,location:map[],description:chararray,street:chararray,city:chararray,country:chararray,jamUuid:chararray,speedKMH:int,length:int,delay:int,blockType:chararray,blockDescription:chararray,blockingAlertUuid:chararray');

-- Remover duplicados basados en todos los campos
data_unique = DISTINCT data;

-- Agrupar por tipo de evento y contar
grouped = GROUP data_unique BY type;
counted = FOREACH grouped GENERATE group as type, COUNT(data_unique) as count;

-- Filtrar eventos por severidad
filtered = FILTER data_unique BY severity > 0;

-- Ordenar por timestamp
sorted = ORDER filtered BY timestamp DESC;

-- Guardar resultados
STORE data_unique INTO '/processing/data_unique';
STORE counted INTO '/processing/event_counts';
STORE filtered INTO '/processing/filtered_events';
STORE sorted INTO '/processing/sorted_events'; 