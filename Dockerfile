# Usamos 3.11-slim para que sea ligero pero compatible
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias de sistema necesarias para compilar algunas librerías de datos
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalamos las librerías del requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código (incluyendo src/ y local_data/)
COPY . .

# Creamos el script de arranque obligatorio
RUN echo "#!/bin/bash\npython src/main.py" > /app/run.sh && \
    chmod +x /app/run.sh

EXPOSE 8000

# AgentBeats a veces busca el run.sh
CMD ["/app/run.sh"]