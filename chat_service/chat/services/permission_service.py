"""
Permission Service.

Validates whether a user may perform an action on a conversation.
Called by both the WebSocket consumer (before accepting the connection)
and by REST API views.

This is the single source of truth for conversation access rules:
  "Only the listing owner AND the applicant/renter may enter a conversation."

Design:
  - All permission checks go through this service, not scattered in consumers/views.
  - Async version provided for the WebSocket consumer (can't block event loop).
"""
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from chat.models import Conversation
from chat.repositories import ConversationRepository

logger = logging.getLogger("chat.services.permission")


class PermissionService:
    """Business logic for conversation access control."""

    @staticmethod
    def can_access_conversation(
        user_id: str, conversation: Conversation
    ) -> bool:
        """
        Return True if user_id is allowed to read/write in this conversation.

        Rules:
          1. User must be owner_id OR renter_id
          2. Conversation must not be blocked (blocked users still can VIEW, not send)
        """
        if not conversation.is_participant(user_id):
            logger.warning(
                "Access denied: user %s is not a participant in conversation %s",
                user_id,
                conversation.id,
            )
            return False
        return True

    @staticmethod
    def can_send_message(
        user_id: str, conversation: Conversation
    ) -> tuple[bool, Optional[str]]:
        """
        Return (allowed, reason) for sending a message.

        Sending is blocked if:
          - User is not a participant
          - Conversation is blocked
        """
        if not conversation.is_participant(user_id):
            return False, "You are not a participant in this conversation"

        if conversation.is_blocked:
            return False, "This conversation has been blocked"

        return True, None

    @staticmethod
    def can_modify_message(user_id: str, sender_id: str) -> bool:
        """
        Only the original sender can edit or delete a message.
        Never trust frontend — always compare against DB sender_id.
        """
        return str(user_id) == str(sender_id)

    # Async wrappers for the WebSocket consumer
    @staticmethod
    async def async_can_access_conversation(
        user_id: str, conversation_id: str
    ) -> tuple[bool, Optional[Conversation]]:
        """
        Async permission check for WebSocket consumers.

        Returns (allowed, conversation) or (False, None).
        Wraps the sync ORM call with sync_to_async.
        """
        conversation = await sync_to_async(
            ConversationRepository.get_by_id
        )(conversation_id)

        if conversation is None:
            logger.warning(
                "WebSocket access denied: conversation %s not found", conversation_id
            )
            return False, None

        allowed = PermissionService.can_access_conversation(user_id, conversation)
        return allowed, conversation if allowed else None
