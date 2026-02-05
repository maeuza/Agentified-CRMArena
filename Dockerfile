FROM python:3.11-slim

# 1. Ajustes de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

# 2. Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. Instalación de librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el código y las DBs (local_data)
COPY . .

# 5. Puerto y Ejecución
# Eliminamos la verificación aquí para evitar errores de sintaxis en el build
EXPOSE 8000

# Tu main.py ya tiene la lógica de importación con try/except, 
# así que fallará ahí con un mensaje claro si algo falta.
CMD ["python3", "src/main.py"]