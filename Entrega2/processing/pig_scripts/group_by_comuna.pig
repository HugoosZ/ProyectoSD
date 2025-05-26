-- Cargar datos desde MongoDB
raw_data = LOAD 'MONGO_URI'
    USING com.mongodb.hadoop.pig.MongoLoader();

-- Agrupar por comuna y tipo de incidente
grouped_data = GROUP raw_data BY (ciudad, tipo);
result = FOREACH grouped_data GENERATE 
    FLATTEN(group) AS (comuna, tipo), 
    COUNT(raw_data) AS total;

-- Guardar resultados en HDFS
STORE result INTO '/output/comuna_analysis' USING PigStorage(',');