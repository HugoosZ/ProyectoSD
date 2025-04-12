FROM python:3.14.0e7-slim

WORKDIR /app

# Instalar dependencias primero para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

CMD ["python", "-u", "src/main.py"]