import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics
from notification.models.notification import NotificationType
from notification.services.notification_service import NotificationService

logger = logging.getLogger("notification.consumer.user")


class UserConsumer(BaseKafkaConsumer):
    """
    Consumes Auth Service events.
    Topic: auth.user.registered
    """
    def __init__(self, group_id: str):
        super().__init__(
            topics=[Topics.AUTH_USER_REGISTERED],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        user_id = payload.get("user_id")

        if not user_id:
            logger.error("Missing user_id in payload: %s", event)
            return

        if event_type == "UserRegistered":
            first_name = payload.get("first_name", "there")
            title = "Welcome to HomeHaven! 🎉"
            message = (
                f"Hi {first_name}, welcome to HomeHaven! "
                "Your account has been created successfully. "
                "Complete your profile to start applying for rentals."
            )

            NotificationService.create_from_event(
                recipient_id=user_id,
                notification_type=NotificationType.SYSTEM,
                title=title,
                message=message,
                payload={"welcome": True},
                source_event_id=event.get("event_id"),
                source_service=event.get("source_service"),
            )
