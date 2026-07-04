"""
Celery application instance for chat_service.

Import path used by the worker command:
    celery -A celery_app worker -Q chat_notifications --loglevel=info

Mirrors the exact pattern from profile_service/celery_app.py.
"""
import os
from celery import Celery

# Tell Celery which Django settings module to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("chat_service")

# Read Celery config from Django settings (keys prefixed with CELERY_)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps (finds chat/tasks/notification_tasks.py)
app.autodiscover_tasks()
