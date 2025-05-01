# ProyectoSD

## Instrucciones para ejecutar el proyecto!!!!!!

### 1. Configurar el generador de tráfico

Abre el archivo:

- `traffic-generator/src/main.py`

Dentro de este archivo puedes:

- Configurar cuántas consultas se desean realizar.
- Elegir el tipo de distribución a utilizar: uniforme o exponencial.

### 2. Crear archivos de entorno

Antes de ejecutar el proyecto, debes crear dos archivos de configuración:

- `mongo.env`
- `redis.env`

Ambos deben seguir el formato definido en `example.env`:

- Las variables relacionadas con MongoDB deben ir en `mongo.env`.
- Las variables relacionadas con Redis deben ir en `redis.env`.

### 3. Configurar Redis

En el archivo `redis.env`, debes asignar el valor de la variable `REDIS_HOST` siguiendo este formato: 

- `tipoDistribucion_políticaRemoción`

Por ejemplo:

``env
REDIS_HOST=uniform-lru


### 4. Modificar el parámetro beta (solo si usas distribución exponencial)

Si se quiere utilizar la distribución exponencial y deseas cambiar el factor de proporcion β (beta), edita el archivo:

- storage/src/mongo_storage.py

donde: 

- Un valor de beta más bajo generará eventos con mayor frecuencia cerca de 0.
- Un valor de beta más alto dispersará más los accesos entre eventos.

### 5. Ejecutar el proyecto

Finalmente, ejecuta el siguiente comando para construir y levantar todos los servicios en contenedores Docker:

- `docker compose up --build`

Este comando compilará y lanzará los servicios definidos en el archivo docker-compose.yml.