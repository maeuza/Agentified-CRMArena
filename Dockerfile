# 1. Usamos una imagen de Python ligera
FROM python:3.10-slim

# 2. Evitamos que Python genere archivos .pyc y forzamos logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 3. Instalamos dependencias del sistema necesarias para algunas librerías
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiamos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del código
COPY . .

# 6. Exponemos el puerto que usa el template (normalmente 8000)
EXPOSE 8000

# 7. Comando para arrancar el agente
# (Asegúrate de que 'src.main:app' coincida con tu archivo de entrada)

CMD ["python", "src/main.py"]