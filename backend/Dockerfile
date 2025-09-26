# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set workdir
WORKDIR /app

# Install system dependencies and CA certificates
RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release && \
    apt-get install -y --reinstall ca-certificates && \
    update-ca-certificates --fresh && \
    rm -rf /var/lib/apt/lists/*
    
# Install dependencies
COPY backend/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY backend /app/

# Run server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
