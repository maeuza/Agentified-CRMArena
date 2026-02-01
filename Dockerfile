# 1. Use a lightweight Python base image
FROM python:3.10-slim

# 2. Prevent Python from writing .pyc files and force real-time logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies required for some Python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python dependencies
# Make sure you have a requirements.txt file in your root folder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Expose the port used by the agent (A2A standard is often 8000)
EXPOSE 8000

# 7. Command to start the agent
# This points to our dual-role entry point
CMD ["python", "src/main.py"]