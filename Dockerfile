# 1. Usamos Bookworm para evitar la inestabilidad de "Trixie"
FROM python:3.11-slim-bookworm

# 2. Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

# 3. Optimización de red para APT y limpieza de cache
# Forzamos IPv4 para evitar que se quede colgado en "delayed item"
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Instalación de dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el código fuente
COPY . .

# 6. Exponemos el puerto y ejecutamos
EXPOSE 8000
CMD ["python3", "src/main.py"]