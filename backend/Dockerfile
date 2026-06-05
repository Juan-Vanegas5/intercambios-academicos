# ============================================================
#  Dockerfile — Backend FastAPI / Intercambios Académicos
#  Build:  docker build -t intercambios-backend .
#  Run:    docker run -p 8001:8001 --env-file .env intercambios-backend
# ============================================================

# Imagen base ligera de Python
FROM python:3.11-slim

# Evita archivos .pyc y habilita logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python primero (aprovecha cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Puerto en el que corre uvicorn
EXPOSE 8001

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
