import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics
from notification.models.notification import NotificationType
from notification.services.notification_service import NotificationService

logger = logging.getLogger("notification.consumer.review")


class ReviewConsumer(BaseKafkaConsumer):
    """
    Consumes Reviews Service events.
    Topic: reviews.review.created
    """

    def __init__(self, group_id: str):
        super().__init__(
            topics=[Topics.REVIEWS_REVIEW_CREATED],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        building_id = payload.get("building_id")

        if not building_id:
            logger.debug("ReviewCreated event has no building_id: %s", event)
            return

        if event_type == "ReviewCreated":
            title = "New Review ⭐"
            review_title = payload.get("title", "A new review has been posted.")
            message = f"A new review was left for a building you manage: {review_title}"

            # Ideally, we should notify the owner of the building.
            # But the payload might only have building_id, so we would either
            # 1. Have building_service listen to this and then notify
            # 2. Assume payload includes the owner_id (we need to make sure the producer adds it, or we fetch it here)
            # For simplicity, if we don't have the recipient, we log a warning.

            # TODO: Modify the producer in reviews_service to include owner_id, or fetch it.
            # We will use a placeholder or check if owner_id is in payload.
            owner_id = payload.get("owner_id")
            if not owner_id:
                logger.warning(
                    "No owner_id in review payload, cannot send notification."
                )
                return

            NotificationService.create_from_event(
                recipient_id=owner_id,
                notification_type=NotificationType.REVIEW,
                title=title,
                message=message,
                payload={
                    "building_id": building_id,
                    "review_id": payload.get("review_id"),
                },
                source_event_id=event.get("event_id"),
                source_service=event.get("source_service"),
            )
