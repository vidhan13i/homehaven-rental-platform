"""
Notification Model
==================
Core model for the notification_service.

Design decisions:
  - UUID primary key (consistent with all other services in the platform)
  - recipient_id stores the Auth User UUID — no FK to User model
    (notification_service has no user model, it's a pure consumer)
  - source_event_id for idempotency: consumers check this before inserting
    to prevent duplicate notifications from Kafka at-least-once delivery
  - payload JSONB stores event-specific data for rich notification rendering
    (e.g., conversation_id for deep-linking, application_id for status lookup)
  - priority field allows UI to render urgent alerts differently
  - Soft archive (is_archived) preserves notification history
"""
import uuid
from django.db import models


class NotificationType(models.TextChoices):
    MESSAGE     = "message",     "Message"
    APPLICATION = "application", "Application"
    REVIEW      = "review",      "Review"
    LISTING     = "listing",     "Listing"
    SYSTEM      = "system",      "System"
    SECURITY    = "security",    "Security"
    CHAT        = "chat",        "Chat"


class NotificationPriority(models.TextChoices):
    LOW    = "low",    "Low"
    NORMAL = "normal", "Normal"
    HIGH   = "high",   "High"
    URGENT = "urgent", "Urgent"


class Notification(models.Model):
    """
    A single notification for one recipient user.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique notification ID.",
    )
    recipient_id = models.UUIDField(
        db_index=True,
        help_text="Auth user UUID of the notification recipient.",
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Event-specific JSON for deep linking and rich display.",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        db_index=True,
    )
    # Idempotency key: Kafka event_id stored here to prevent duplicates
    source_event_id = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        help_text="Kafka event_id; used to ensure exactly-once notification creation.",
    )
    source_service = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Which service published the triggering event.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "notification"
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient_id", "is_read", "-created_at"],
                name="notif_recipient_unread_idx",
            ),
            models.Index(
                fields=["recipient_id", "notification_type"],
                name="notif_recipient_type_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.notification_type}] {self.title} → {self.recipient_id}"

    @property
    def is_unread(self) -> bool:
        return not self.is_read
