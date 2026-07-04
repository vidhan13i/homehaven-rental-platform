import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics
from notification.models.notification import NotificationType, NotificationPriority
from notification.services.notification_service import NotificationService

logger = logging.getLogger("notification.consumer.message")


class MessageConsumer(BaseKafkaConsumer):
    """
    Consumes Chat Service events.
    Topic: chat.message.sent
    """

    def __init__(self, group_id: str):
        super().__init__(
            topics=[Topics.CHAT_MESSAGE_SENT],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        recipient_id = payload.get("recipient_id")

        if not recipient_id:
            logger.debug(
                "MessageSent event has no recipient_id (e.g. system message): %s", event
            )
            return

        if event_type == "MessageSent":
            title = "New Message 💬"
            content_preview = payload.get(
                "content_preview", "You received a new message."
            )
            conversation_id = payload.get("conversation_id")

            NotificationService.create_from_event(
                recipient_id=recipient_id,
                notification_type=NotificationType.MESSAGE,
                title=title,
                message=content_preview,
                payload={"conversation_id": conversation_id},
                priority=NotificationPriority.HIGH,
                source_event_id=event.get("event_id"),
                source_service=event.get("source_service"),
            )
