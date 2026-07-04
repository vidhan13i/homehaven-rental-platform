"""
Celery application for notification_service.
Handles:
  - Email delivery tasks (queue: email_delivery)
  - General notification tasks (queue: notifications)
"""

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("notification_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
