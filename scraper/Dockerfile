FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias necesarias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de requerimientos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la app
COPY . .

# Ejecutar script principal
CMD ["python", "-u", "src/main.py"]