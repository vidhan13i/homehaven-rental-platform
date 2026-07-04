"""
Notification Django App Configuration
"""

from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = "django.db.models.UUIDField"
    name = "notification"
    label = "notification"

    def ready(self):
        # Import signal handlers and ensure app is fully initialized
        pass
