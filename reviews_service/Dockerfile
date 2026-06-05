FROM python:3.12-slim

WORKDIR /app

# PYTHONDONTWRITEBYTECODE: No .pyc files (keeps container clean)
# PYTHONUNBUFFERED: Logs appear immediately in docker compose logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install deps BEFORE copying code (Docker layer caching = faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# gunicorn: production-grade WSGI server (replaces "python manage.py runserver")
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "config.wsgi:application"]
