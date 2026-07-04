"""
Notification Repository
=======================
Encapsulates all database access for Notification and NotificationPreference.

Design (Repository Pattern):
  - No business logic here — only raw DB operations
  - Service layer calls repository methods
  - All queries use the 'notification' database alias via the DB router
  - Idempotency: create_if_not_exists() prevents duplicate notifications
    when Kafka delivers the same event twice (at-least-once guarantee)
"""
import logging
import uuid
from typing import Optional, List, Tuple
from django.utils import timezone
from django.db import IntegrityError

from notification.models import Notification, NotificationPreference, NotificationType

logger = logging.getLogger("notification.repository")


class NotificationRepository:
    """CRUD operations for Notification model."""

    @staticmethod
    def create(
        recipient_id: str,
        notification_type: str,
        title: str,
        message: str,
        payload: dict = None,
        priority: str = "normal",
        source_event_id: str = None,
        source_service: str = "",
    ) -> Optional[Notification]:
        """
        Create a new notification.

        Uses get_or_create on source_event_id for idempotency.
        If a notification with the same source_event_id already exists,
        returns None (duplicate silently dropped).
        """
        try:
            create_kwargs = {
                "recipient_id": uuid.UUID(str(recipient_id)),
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "payload": payload or {},
                "priority": priority,
                "source_service": source_service,
            }
            if source_event_id:
                notification, created = Notification.objects.using("notification").get_or_create(
                    source_event_id=uuid.UUID(str(source_event_id)),
                    defaults=create_kwargs,
                )
                if not created:
                    logger.info(
                        "Duplicate notification dropped | source_event_id=%s",
                        source_event_id,
                    )
                    return None
                return notification
            else:
                return Notification.objects.using("notification").create(**create_kwargs)

        except IntegrityError as exc:
            logger.warning("Notification creation IntegrityError (likely duplicate): %s", exc)
            return None
        except Exception as exc:
            logger.error("Failed to create notification: %s", exc)
            return None

    @staticmethod
    def get_for_user(
        user_id: str,
        notification_type: str = None,
        is_read: bool = None,
        is_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Notification], int]:
        """
        Get paginated notifications for a user.
        Returns (queryset, total_count).
        """
        qs = Notification.objects.using("notification").filter(
            recipient_id=user_id,
            is_archived=is_archived,
        )
        if notification_type:
            qs = qs.filter(notification_type=notification_type)
        if is_read is not None:
            qs = qs.filter(is_read=is_read)

        total = qs.count()
        return qs.order_by("-created_at")[offset : offset + limit], total

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread, non-archived notifications for a user."""
        return Notification.objects.using("notification").filter(
            recipient_id=user_id,
            is_read=False,
            is_archived=False,
        ).count()

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> Optional[Notification]:
        """Mark a single notification as read. Enforces recipient ownership."""
        try:
            notification = Notification.objects.using("notification").get(
                id=notification_id,
                recipient_id=user_id,
            )
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save(using="notification", update_fields=["is_read", "read_at"])
            return notification
        except Notification.DoesNotExist:
            return None

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        """Mark all unread notifications as read for a user. Returns count updated."""
        return Notification.objects.using("notification").filter(
            recipient_id=user_id,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())

    @staticmethod
    def archive(notification_id: str, user_id: str) -> Optional[Notification]:
        """Archive a notification (soft delete). Enforces recipient ownership."""
        try:
            notification = Notification.objects.using("notification").get(
                id=notification_id,
                recipient_id=user_id,
            )
            notification.is_archived = True
            notification.archived_at = timezone.now()
            notification.save(using="notification", update_fields=["is_archived", "archived_at"])
            return notification
        except Notification.DoesNotExist:
            return None

    @staticmethod
    def delete(notification_id: str, user_id: str) -> bool:
        """Hard delete a notification. Enforces recipient ownership. Returns True if deleted."""
        deleted, _ = Notification.objects.using("notification").filter(
            id=notification_id,
            recipient_id=user_id,
        ).delete()
        return deleted > 0

    @staticmethod
    def get_by_id(notification_id: str, user_id: str) -> Optional[Notification]:
        """Get a single notification by ID, scoped to the requesting user."""
        try:
            return Notification.objects.using("notification").get(
                id=notification_id,
                recipient_id=user_id,
            )
        except Notification.DoesNotExist:
            return None


class PreferenceRepository:
    """CRUD operations for NotificationPreference model."""

    @staticmethod
    def get_or_create_for_user(user_id: str) -> NotificationPreference:
        """
        Get existing preferences or create default preferences for a user.
        Called lazily — preferences are created on first notification delivery.
        """
        pref, _ = NotificationPreference.objects.using("notification").get_or_create(
            user_id=user_id,
        )
        return pref

    @staticmethod
    def update(user_id: str, **kwargs) -> Optional[NotificationPreference]:
        """Update notification preferences for a user."""
        try:
            pref = NotificationPreference.objects.using("notification").get(user_id=user_id)
            for key, value in kwargs.items():
                if hasattr(pref, key):
                    setattr(pref, key, value)
            pref.save(using="notification")
            return pref
        except NotificationPreference.DoesNotExist:
            return None
