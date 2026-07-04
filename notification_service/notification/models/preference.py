"""
NotificationPreference Model
============================
Per-user notification delivery preferences.

When a Kafka event arrives, the notification service checks these preferences
before delivering via each channel. If the user has disabled email for messages,
the Celery email task is simply not queued.

One row per user. Created automatically when a user's first notification is
triggered (lazy creation with get_or_create).
"""

import uuid
from django.db import models


class NotificationPreference(models.Model):
    """
    User notification delivery preferences — one row per user.
    All channels default to enabled for new users.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(
        unique=True,
        db_index=True,
        help_text="Auth user UUID — one preference row per user.",
    )

    # ── In-App Notifications ───────────────────────────────────────────────
    inapp_enabled = models.BooleanField(default=True)
    inapp_messages = models.BooleanField(default=True)
    inapp_applications = models.BooleanField(default=True)
    inapp_reviews = models.BooleanField(default=True)
    inapp_listings = models.BooleanField(default=True)
    inapp_system = models.BooleanField(default=True)

    # ── Email Notifications ────────────────────────────────────────────────
    email_enabled = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=True)
    email_applications = models.BooleanField(default=True)
    email_reviews = models.BooleanField(default=True)
    email_listings = models.BooleanField(default=True)
    email_system = models.BooleanField(default=True)

    # ── Push Notifications (interface ready, not yet implemented) ──────────
    push_enabled = models.BooleanField(
        default=False,
        help_text="Push notifications — interface ready, implementation pending.",
    )

    # ── SMS (interface ready, not yet implemented) ─────────────────────────
    sms_enabled = models.BooleanField(
        default=False,
        help_text="SMS notifications — interface ready, implementation pending.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "notification"
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"NotificationPreference(user={self.user_id})"

    def allows_inapp(self, notification_type: str) -> bool:
        """Check if in-app notifications are enabled for a given type."""
        if not self.inapp_enabled:
            return False
        type_map = {
            "message": self.inapp_messages,
            "chat": self.inapp_messages,
            "application": self.inapp_applications,
            "review": self.inapp_reviews,
            "listing": self.inapp_listings,
            "system": self.inapp_system,
            "security": self.inapp_system,
        }
        return type_map.get(notification_type, True)

    def allows_email(self, notification_type: str) -> bool:
        """Check if email notifications are enabled for a given type."""
        if not self.email_enabled:
            return False
        type_map = {
            "message": self.email_messages,
            "chat": self.email_messages,
            "application": self.email_applications,
            "review": self.email_reviews,
            "listing": self.email_listings,
            "system": self.email_system,
            "security": self.email_system,
        }
        return type_map.get(notification_type, True)
