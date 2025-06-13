# Usa una imagen de Python liviana
FROM python:3.9-slim

# Directorio de trabajo en el contenedor
WORKDIR /app/storage

# Copiar los requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente
COPY src/ .

# Comando que se ejecutará al levantar el contenedor
CMD ["python", "mongo_storage.py"]
