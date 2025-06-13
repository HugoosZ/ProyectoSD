# ProyectoSD - Entrega 2 

## Descripción

Este proyecto implementa un sistema distribuido que utiliza Apache Pig y Hadoop para el procesamiento de datos, junto con un servicio de almacenamiento (mongo). Los servicios se orquestan mediante Docker Compose.

## Requisitos previos

- Arquitectura ARM64 (la imagen de Java utilizada es específica para ARM64; si tu equipo no cuenta con esta arquitectura, el código no funcionará).

## Inicialización del sistema

Al iniciar los contenedores, el sistema se lanza de forma secuencial utilizando las dependencias definidas en `docker-compose.yml`:

1. Se inicia primero el servicio de MongoDB.
2. Posteriormente, se levantan los demás componentes.
3. El contenedor `waze-processing` realiza intentos de conexión hasta que el `namenode` de Hadoop sale del modo seguro. Una vez disponible, se conecta y ejecuta los comandos de Pig definidos en `processing/src/main.py`.

## Ejecución del proyecto

Para construir y levantar todos los servicios en contenedores Docker, ejecuta el siguiente comando desde la carpeta `Entrega2/`:

```sh
docker compose up --build
```

Este comando compilará y lanzará los servicios definidos en el archivo `docker-compose.yml`.

## Notas adicionales

- Si necesitas modificar la configuración de Hadoop o Pig, revisa los archivos en `processing/hadoop-conf/` y `processing/src/pig/`.
- Los resultados del procesamiento se almacenan en la carpeta `processing/results/`.
- Si tienes problemas con Hadoop, prueba borrando el contenido de la carpeta `/hadoop-data/`.
- Para detener los servicios, puedes usar:

```sh
docker compose down
```

---



Si tienes dudas o problemas, revisa los logs de los contenedores para obtener más información sobre posibles errores.