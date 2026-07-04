"""
Notification Service (Business Logic Layer)
===========================================
Orchestrates notification creation, delivery, and state management.

Flow:
  1. Kafka consumer calls NotificationService.create_from_event()
  2. Service checks preferences (PreferenceRepository)
  3. Service stores notification (NotificationRepository)
  4. Service delivers via enabled channels (DeliveryService)
  5. Service pushes to WebSocket via Channel Layer
"""

import logging
from typing import Optional, List, Tuple

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notification.models import Notification, NotificationPriority
from notification.repositories.notification_repository import (
    NotificationRepository,
    PreferenceRepository,
)

logger = logging.getLogger("notification.service")


class NotificationService:
    """Core business logic for notification creation and delivery."""

    @staticmethod
    def create_from_event(
        recipient_id: str,
        notification_type: str,
        title: str,
        message: str,
        payload: dict = None,
        priority: str = NotificationPriority.NORMAL,
        source_event_id: str = None,
        source_service: str = "",
        send_email: bool = True,
    ) -> Optional[Notification]:
        """
        Main entry point called by Kafka consumers.

        Creates the notification in the DB, then:
          1. Pushes it to the user's WebSocket channel (if connected)
          2. Queues an email delivery task (if preferences allow + send_email=True)

        Returns the created Notification or None if it was a duplicate.
        """
        # Step 1: Check user notification preferences
        prefs = PreferenceRepository.get_or_create_for_user(recipient_id)
        if not prefs.allows_inapp(notification_type):
            logger.info(
                "In-app notifications disabled for user=%s type=%s",
                recipient_id,
                notification_type,
            )
            return None

        # Step 2: Store notification (idempotent via source_event_id)
        notification = NotificationRepository.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            payload=payload or {},
            priority=priority,
            source_event_id=source_event_id,
            source_service=source_service,
        )

        if notification is None:
            # Duplicate event — already processed
            return None

        logger.info(
            "Notification created | id=%s | recipient=%s | type=%s",
            notification.id,
            recipient_id,
            notification_type,
        )

        # Step 3: Real-time WebSocket push
        NotificationService._push_to_websocket(notification)

        # Step 4: Queue email delivery via Celery (if prefs allow)
        if send_email and prefs.allows_email(notification_type):
            from notification.tasks.email_tasks import send_notification_email

            send_notification_email.apply_async(
                args=[str(notification.id), str(recipient_id)],
                queue="email_delivery",
            )

        return notification

    @staticmethod
    def _push_to_websocket(notification: Notification) -> None:
        """
        Push the notification to the user's WebSocket channel group.
        The group name pattern is: notifications_{user_id}
        If the user is not connected, the message is silently dropped
        (they'll see it when they reconnect and fetch via REST API).
        """
        try:
            channel_layer = get_channel_layer()
            group_name = f"notifications_{notification.recipient_id}"

            notification_data = {
                "id": str(notification.id),
                "type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "payload": notification.payload,
                "priority": notification.priority,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send.notification",
                    "notification": notification_data,
                },
            )
            logger.debug(
                "WebSocket push sent | group=%s | notification_id=%s",
                group_name,
                notification.id,
            )
        except Exception as exc:
            # WebSocket push failure must never block the consumer thread
            logger.error(
                "WebSocket push failed | notification_id=%s | error=%s",
                notification.id,
                exc,
            )

    @staticmethod
    def mark_as_read(notification_id: str, user_id: str) -> Optional[Notification]:
        return NotificationRepository.mark_as_read(notification_id, user_id)

    @staticmethod
    def mark_all_as_read(user_id: str) -> int:
        return NotificationRepository.mark_all_as_read(user_id)

    @staticmethod
    def archive(notification_id: str, user_id: str) -> Optional[Notification]:
        return NotificationRepository.archive(notification_id, user_id)

    @staticmethod
    def delete(notification_id: str, user_id: str) -> bool:
        return NotificationRepository.delete(notification_id, user_id)

    @staticmethod
    def get_for_user(
        user_id: str,
        notification_type: str = None,
        is_read: bool = None,
        is_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Notification], int]:
        return NotificationRepository.get_for_user(
            user_id=user_id,
            notification_type=notification_type,
            is_read=is_read,
            is_archived=is_archived,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        return NotificationRepository.get_unread_count(user_id)
