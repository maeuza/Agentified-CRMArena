FROM python:3.11-slim

# Evita que Python genere archivos .pyc y asegura que los logs salgan rápido
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configuramos la ruta para que encuentre tanto tus archivos en 'src' como las librerías
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

# Instalamos herramientas básicas de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Primero copiamos e instalamos dependencias (esto es lo más pesado)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "a2a-sdk[http-server]"

# Luego copiamos el resto de tu código
COPY . .

# --- PASO DE SEGURIDAD ---
# Si esto falla aquí, el build se detiene y no subes una imagen rota a GitHub
RUN python3 -c "from a2a.server.app import AgentServer; print('✅ SDK y Servidor encontrados')"

EXPOSE 8000

# Arrancamos directamente el script principal
CMD ["python3", "src/main.py"]