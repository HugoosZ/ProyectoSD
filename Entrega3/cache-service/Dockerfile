# cache-service/Dockerfile
FROM python:3.9-slim

WORKDIR /app/cache-service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/ /app/cache-service/

CMD ["python", "-u", "main.py"]