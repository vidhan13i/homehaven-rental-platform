import logging
from typing import Dict, Any

from shared_lib.kafka.consumer import BaseKafkaConsumer
from shared_lib.kafka.topics import Topics
from chat.services.conversation_service import ConversationService

logger = logging.getLogger("chat.consumer.application")


class ApplicationApprovedConsumer(BaseKafkaConsumer):
    """
    Consumes Applications Service events.
    Topic: applications.application.approved
    
    When an application is approved, we automatically create a conversation
    between the renter and the agent, if one doesn't already exist.
    """
    def __init__(self, group_id: str):
        super().__init__(
            topics=[Topics.APPLICATIONS_APPROVED],
            group_id=group_id,
        )

    def handle(self, event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        
        if event_type != "ApplicationApproved":
            return

        renter_id = payload.get("renter_id")
        agent_id = payload.get("agent_id")
        application_id = payload.get("application_id")

        if not renter_id or not agent_id:
            logger.warning(
                "Missing renter_id or agent_id in ApplicationApproved event: %s",
                event
            )
            return
            
        if renter_id == agent_id:
            logger.info("Renter and agent are the same person; skipping conversation creation.")
            return

        logger.info(
            "Application %s approved. Auto-creating conversation between renter=%s and agent=%s",
            application_id, renter_id, agent_id
        )

        try:
            # Get or create conversation (is_direct=True by default for 1:1)
            conversation = ConversationService.get_or_create_direct_conversation(
                user1_id=renter_id,
                user2_id=agent_id
            )
            logger.info("Conversation ready: %s", conversation.id)
            
            # Send a system message welcoming them? (Optional)
            # We don't have a strict system user, but we can send it as the agent
            # or just leave the conversation empty for them to start.
            
        except Exception as exc:
            logger.error(
                "Failed to auto-create conversation for application %s: %s",
                application_id, exc
            )
            raise  # bubble up to trigger retry logic
