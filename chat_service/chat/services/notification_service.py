"""
Notification Service.

Decides whether to queue an offline notification for a message recipient.
Called by the consumer after a message is sent.

Architecture:
  - Check if recipient is online (presence service)
  - If offline → queue a Celery task (notification_tasks.notify_offline_user)
  - The Celery task handles the actual delivery (email, push, SMS — future)

This service is the bridge between real-time (WebSocket) and async (Celery).
"""
import logging
from typing import Optional

from chat.models import Message, Conversation
from chat.services.presence_service import PresenceService

logger = logging.getLogger("chat.services.notification")


class NotificationService:
    """Decides and dispatches offline user notifications."""

    @staticmethod
    def notify_if_offline(
        message: Message,
        conversation: Conversation,
    ) -> None:
        """
        Check if the recipient is offline and queue a notification if so.

        Synchronous version — called from REST views or Celery tasks.
        """
        recipient_id = conversation.get_other_participant(str(message.sender_id))
        if not recipient_id:
            return

        if not PresenceService.is_online(recipient_id):
            NotificationService._queue_notification(
                recipient_id=recipient_id,
                message_id=str(message.id),
                conversation_id=str(conversation.id),
                sender_username=None,  # Will be resolved in the task
                preview=message.content[:100] if not message.is_deleted else "",
            )

    @staticmethod
    def _queue_notification(
        recipient_id: str,
        message_id: str,
        conversation_id: str,
        sender_username: Optional[str],
        preview: str,
    ) -> None:
        """Queue a Celery task for offline notification delivery."""
        try:
            from chat.tasks.notification_tasks import notify_offline_user
            notify_offline_user.apply_async(
                kwargs={
                    "recipient_id": recipient_id,
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "sender_username": sender_username,
                    "preview": preview,
                },
                queue="chat_notifications",
                countdown=2,  # Small delay to avoid spurious notifications if user reconnects
            )
            logger.info(
                "Queued offline notification for user %s (message %s)",
                recipient_id,
                message_id,
            )
        except Exception as exc:
            # Never let notification failure block message delivery
            logger.error(
                "Failed to queue notification for user %s: %s",
                recipient_id, str(exc),
            )

    @staticmethod
    async def async_notify_if_offline(
        message: Message,
        conversation: Conversation,
    ) -> None:
        """
        Async version for WebSocket consumer.
        Runs the sync notification logic in a thread pool.
        """
        from asgiref.sync import sync_to_async
        await sync_to_async(NotificationService.notify_if_offline)(
            message, conversation
        )
