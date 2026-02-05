FROM python:3.11-slim

# Configuraciones de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# PYTHONPATH para que encuentre los módulos en 'src' y las DBs
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

# Instalamos dependencias de compilación para pandas/pydantic
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Instalamos las librerías (Capa pesada pero se cachea)
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Copiamos todo el código (Incluye src/local_data con tus .db)
COPY . .

# 3. VERIFICACIÓN: Probamos si el SDK está bien instalado
# Si este paso falla, es que la versión del SDK en PyPI tiene un problema de estructura
RUN python3 -c "import a2a; from a2a.server.app import AgentServer; print('✅ SDK y Servidor cargados con éxito')"

EXPOSE 8000

# Ejecutamos desde la carpeta src
CMD ["python3", "src/main.py"]