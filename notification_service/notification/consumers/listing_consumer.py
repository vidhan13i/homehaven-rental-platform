import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics

logger = logging.getLogger("notification.consumer.listing")


class ListingConsumer(BaseKafkaConsumer):
    """
    Consumes Listings Service events.
    Topic: listings.listing.created
    """

    def __init__(self, group_id: str):
        super().__init__(
            topics=[Topics.LISTINGS_LISTING_CREATED],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})

        # Currently, ListingCreated doesn't explicitly have a notification target unless we want to notify admins or the agent who created it.
        # But for now, we just log it or notify the system admins.
        # If we have a robust search/saved-searches feature, this would notify users whose saved search matches this listing.

        logger.info("Consumed Listing event: %s", event_type)

        # We won't generate a direct notification for this unless we have a specific recipient.
        pass
