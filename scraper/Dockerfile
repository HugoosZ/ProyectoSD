FROM python:3.9-slim

# Instalar dependencias del sistema para Chrome
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    chromium \
    chromium-driver \
    # Dependencias adicionales requeridas
    gcc \
    g++ \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "src/main.py"]