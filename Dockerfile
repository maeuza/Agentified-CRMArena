FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app:/app/src"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero el archivo de requisitos
COPY requirements.txt .

# Instalamos pip actualizado y las librerías del archivo
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

EXPOSE 8000
CMD ["python3", "src/main.py"]