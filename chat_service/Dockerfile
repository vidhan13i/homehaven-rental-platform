FROM python:3.12-slim

WORKDIR /app

# PYTHONDONTWRITEBYTECODE: No .pyc files
# PYTHONUNBUFFERED: Logs appear immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Daphne: production-grade ASGI server required for concurrent WebSocket connections.
# Django's runserver is single-threaded and cannot handle multiple WS clients in parallel.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
