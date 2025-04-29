# Imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY requirements.txt .
COPY src/ src/

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Definir variable de entorno para producción
ENV PYTHONUNBUFFERED=1

# Comando de ejecución
CMD ["python", "src/main.py"]
