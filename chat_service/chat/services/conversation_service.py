"""
Conversation Service.

Business logic for conversation lifecycle operations.
Calls ConversationRepository for DB access.
Calls shared_lib.resilience for inter-service HTTP calls.
"""

import logging
from typing import Optional

import requests

from chat.models import Conversation
from chat.repositories import ConversationRepository

try:
    from shared_lib.resilience import make_resilient_request
except ImportError:
    # Fallback for local development outside Docker
    def make_resilient_request(url, method="GET", service_name="", **kwargs):
        return requests.request(method, url, **kwargs)


logger = logging.getLogger("chat.services.conversation")


class ConversationService:
    """Business logic for conversation operations."""

    @staticmethod
    def create_conversation(
        listing_id: str,
        owner_id: str,
        renter_id: str,
        requesting_user_id: str,
    ) -> tuple[Conversation, bool]:
        """
        Create a conversation between an owner and a renter for a specific listing.

        Validates:
          1. requesting_user_id must be either owner_id or renter_id
          2. owner_id != renter_id (can't message yourself)

        Returns (conversation, created) where created=False if it already existed.
        """
        if owner_id == renter_id:
            raise ValueError("Owner and renter cannot be the same user")

        requesting = str(requesting_user_id)
        if requesting not in (str(owner_id), str(renter_id)):
            raise PermissionError(
                "You can only start a conversation as the owner or the renter"
            )

        conversation, created = ConversationRepository.create(
            listing_id=listing_id,
            owner_id=owner_id,
            renter_id=renter_id,
        )

        if created:
            logger.info(
                "Conversation %s created for listing %s between owner=%s and renter=%s",
                conversation.id,
                listing_id,
                owner_id,
                renter_id,
            )

        return conversation, created

    @staticmethod
    def get_conversation(conversation_id: str, user_id: str) -> Optional[Conversation]:
        """
        Fetch a conversation, ensuring the user is a participant.
        Returns None if not found or not authorized.
        """
        conversation = ConversationRepository.get_by_id(conversation_id)
        if conversation is None:
            return None
        if not conversation.is_participant(user_id):
            logger.warning(
                "User %s attempted to access conversation %s — not a participant",
                user_id,
                conversation_id,
            )
            return None
        return conversation

    @staticmethod
    def list_conversations(user_id: str, include_archived: bool = False) -> list:
        """Return all conversations for a user, ordered by latest activity."""
        return list(
            ConversationRepository.get_for_user(
                user_id=user_id,
                include_archived=include_archived,
            )
        )

    @staticmethod
    def archive_conversation(
        conversation_id: str, user_id: str, archived: bool = True
    ) -> bool:
        """Toggle archive state. Only participants can archive."""
        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation or not conversation.is_participant(user_id):
            return False
        return ConversationRepository.set_archived(conversation_id, archived)

    @staticmethod
    def pin_conversation(
        conversation_id: str, user_id: str, pinned: bool = True
    ) -> bool:
        """Toggle pin state. Only participants can pin."""
        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation or not conversation.is_participant(user_id):
            return False
        return ConversationRepository.set_pinned(conversation_id, pinned)

    @staticmethod
    def block_conversation(
        conversation_id: str, user_id: str, blocked: bool = True
    ) -> bool:
        """
        Block or unblock a conversation.
        Only a participant can block.
        When blocked, new messages cannot be sent.
        """
        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation or not conversation.is_participant(user_id):
            return False
        return ConversationRepository.set_blocked(
            conversation_id, blocked, blocked_by=user_id if blocked else None
        )

    @staticmethod
    def delete_conversation(conversation_id: str, user_id: str) -> bool:
        """Delete a conversation (hard delete — only participants)."""
        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation or not conversation.is_participant(user_id):
            return False
        return ConversationRepository.delete(conversation_id)
