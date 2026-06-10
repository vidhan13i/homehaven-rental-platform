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

# Use runserver in dev for static files and auto-reloading
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
