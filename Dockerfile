FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# NUEVO: Forzamos a Python a reconocer la carpeta raíz y src para los módulos
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Actualizamos pip e instalamos TODO
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Verificación de seguridad: Crea el script asegurando que use python3
RUN echo "#!/bin/bash\npython3 src/main.py" > /app/run.sh && \
    chmod +x /app/run.sh

EXPOSE 8000
CMD ["/app/run.sh"]