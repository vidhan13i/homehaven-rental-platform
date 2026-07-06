"""
Celery application instance for profile_service.

Import path used by Django's CELERY_APP setting and the worker CMD:
    celery -A celery_app worker ...
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("profile_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
