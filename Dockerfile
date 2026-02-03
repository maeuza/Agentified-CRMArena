FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="."

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalación base y FORZAMOS el extra del servidor
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "a2a-sdk[http-server]"

COPY . .

# Verificación de la ruta completa
RUN python3 -c "import a2a.server.app; from a2a.server.app import AgentServer; print('✅ SDK y Servidor encontrados')"

EXPOSE 8000
CMD ["python3", "src/main.py"]