
-- Cargar datos limpios
data = LOAD '/processing/data_unique' USING PigStorage(',') 
    AS (tipo:chararray, subtipo:chararray, ubicacion:chararray, ciudad:chararray, hora:chararray, lat:float, lon:float);

-- Análisis por comuna
group_by_ciudad = GROUP data BY ciudad;
count_by_ciudad = FOREACH group_by_ciudad GENERATE 
    group AS ciudad, 
    COUNT(data) AS total,
    COUNT_STAR(data) AS cantidad_incidentes;
STORE count_by_ciudad INTO '/processing/incidentes_por_comuna' USING PigStorage(',');

-- Análisis por ciudad y tipo
group_by_ciudad_tipo = GROUP data BY (ciudad, tipo);
count_by_ciudad_tipo = FOREACH group_by_ciudad_tipo GENERATE 
    FLATTEN(group) AS (ciudad, tipo), 
    COUNT(data) AS total;
STORE count_by_ciudad_tipo INTO '/processing/incidentes_ciudad_tipo' USING PigStorage(',');

-- Conteo por tipo
group_by_tipo = GROUP data BY tipo;
count_by_tipo = FOREACH group_by_tipo GENERATE 
    group AS tipo, 
    COUNT(data) AS total;
STORE count_by_tipo INTO '/processing/event_counts' USING PigStorage(',');

-- Análisis temporal por día 
data_con_fecha = FOREACH data GENERATE
    tipo,
    subtipo,
    ciudad,
    SUBSTRING(hora, 0, 10) AS fecha,
    hora;

data_con_fecha_valida = FILTER data_con_fecha BY fecha MATCHES '\\d{4}-\\d{2}-\\d{2}';

-- Evolución diaria
group_by_fecha = GROUP data_con_fecha_valida BY fecha;
count_by_fecha = FOREACH group_by_fecha GENERATE 
    group AS fecha, 
    COUNT(data_con_fecha_valida) AS total_incidentes;
STORE count_by_fecha INTO '/processing/evolucion_temporal_diaria' USING PigStorage(',');

-- Evolución por tipo
group_by_fecha_tipo = GROUP data_con_fecha_valida BY (fecha, tipo);
count_by_fecha_tipo = FOREACH group_by_fecha_tipo GENERATE 
    FLATTEN(group) AS (fecha, tipo), 
    COUNT(data_con_fecha_valida) AS total;
STORE count_by_fecha_tipo INTO '/processing/evolucion_por_tipo' USING PigStorage(',');

-- Análisis por hora
data_con_hora_dia = FOREACH data GENERATE
    tipo,
    ciudad,
    REGEX_EXTRACT(hora, '.*T(\\d{2}):\\d{2}:\\d{2}', 1) AS hora_dia;

data_con_hora_valida = FILTER data_con_hora_dia BY hora_dia IS NOT NULL AND hora_dia != '';

-- Distribución horaria
group_by_hora = GROUP data_con_hora_valida BY hora_dia;
count_by_hora = FOREACH group_by_hora GENERATE 
    group AS hora_dia, 
    COUNT(data_con_hora_valida) AS total_incidentes;
STORE count_by_hora INTO '/processing/distribucion_horaria' USING PigStorage(',');

-- Horas pico por tipo
group_by_hora_tipo = GROUP data_con_hora_valida BY (hora_dia, tipo);
count_by_hora_tipo = FOREACH group_by_hora_tipo GENERATE 
    FLATTEN(group) AS (hora_dia, tipo), 
    COUNT(data_con_hora_valida) AS total;
STORE count_by_hora_tipo INTO '/processing/picos_por_hora_tipo' USING PigStorage(',');