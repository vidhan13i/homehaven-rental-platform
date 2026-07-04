FROM python:3.12-slim

WORKDIR /app

# Install librdkafka system dependency required by confluent-kafka
RUN apt-get update && apt-get install -y \
    gcc \
    librdkafka-dev \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Daphne runs the ASGI app — required for WebSocket (Django Channels) support
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
