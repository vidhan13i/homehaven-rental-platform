# This makes Django load the Celery app when the service starts,
# so shared_task decorators work correctly across all apps.
from celery_app import app as celery_app

__all__ = ('celery_app',)
