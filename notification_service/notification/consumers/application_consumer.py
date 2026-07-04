import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics
from notification.models.notification import NotificationType
from notification.services.notification_service import NotificationService

logger = logging.getLogger("notification.consumer.application")


class ApplicationConsumer(BaseKafkaConsumer):
    """
    Consumes Application Service events.
    Topics: applications.application.created, approved, rejected
    """
    def __init__(self, group_id: str):
        super().__init__(
            topics=[
                Topics.APPLICATIONS_CREATED,
                Topics.APPLICATIONS_APPROVED,
                Topics.APPLICATIONS_REJECTED,
            ],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        application_id = payload.get("application_id")
        renter_id = payload.get("renter_id")

        if not renter_id:
            logger.warning("No renter_id in application event: %s", event)
            return

        title = ""
        message = ""

        if event_type == "ApplicationCreated":
            title = "Application Submitted 📄"
            message = f"Your application ({application_id[:8]}) has been submitted successfully and is pending review."
        elif event_type == "ApplicationApproved":
            title = "Application Approved! 🎉"
            message = f"Congratulations! Your application ({application_id[:8]}) has been approved."
        elif event_type == "ApplicationRejected":
            title = "Application Update 📄"
            message = f"Your application ({application_id[:8]}) has been rejected. Keep looking for other great places!"
        else:
            return

        NotificationService.create_from_event(
            recipient_id=renter_id,
            notification_type=NotificationType.APPLICATION,
            title=title,
            message=message,
            payload={"application_id": application_id},
            source_event_id=event.get("event_id"),
            source_service=event.get("source_service"),
        )
