"""
Conversation Repository.

Encapsulates all database access for Conversation objects.
Services call this repository; views/consumers never query the ORM directly.

Repository Pattern benefits:
  - Single place to change query optimizations (select_related, prefetch, indexes)
  - Testable in isolation with a mock
  - Services remain DB-agnostic
"""

import logging
import uuid
from typing import Optional

from django.db import IntegrityError
from django.utils import timezone

from chat.models import Conversation

logger = logging.getLogger("chat.repositories.conversation")


class ConversationRepository:
    """Data access layer for Conversation objects."""

    @staticmethod
    def get_by_id(conversation_id: str) -> Optional[Conversation]:
        """Fetch a conversation by UUID. Returns None if not found."""
        try:
            return Conversation.objects.get(id=conversation_id)
        except (Conversation.DoesNotExist, ValueError):
            return None

    @staticmethod
    def get_for_user(user_id: str, include_archived: bool = False) -> list:
        """
        Fetch all conversations where user is owner or renter.
        Ordered by last_message_at DESC (most recent first).
        """
        qs = Conversation.objects.filter(
            **{"is_archived": False} if not include_archived else {}
        ).filter(
            # Django ORM: owner_id=user_id OR renter_id=user_id
        )
        from django.db.models import Q

        qs = Conversation.objects.filter(Q(owner_id=user_id) | Q(renter_id=user_id))
        if not include_archived:
            qs = qs.filter(is_archived=False)
        return qs.order_by("-is_pinned", "-last_message_at", "-created_at")

    @staticmethod
    def get_by_listing_and_participants(
        listing_id: str, owner_id: str, renter_id: str
    ) -> Optional[Conversation]:
        """Look up an existing conversation by the unique triple (listing, owner, renter)."""
        try:
            return Conversation.objects.get(
                listing_id=listing_id,
                owner_id=owner_id,
                renter_id=renter_id,
            )
        except Conversation.DoesNotExist:
            return None

    @staticmethod
    def create(
        listing_id: str,
        owner_id: str,
        renter_id: str,
    ) -> tuple[Conversation, bool]:
        """
        Create a new conversation. Returns (conversation, created).
        If a conversation already exists for this triple, returns the existing one.
        """
        try:
            obj, created = Conversation.objects.get_or_create(
                listing_id=uuid.UUID(str(listing_id)),
                owner_id=uuid.UUID(str(owner_id)),
                renter_id=uuid.UUID(str(renter_id)),
            )
            return obj, created
        except IntegrityError as exc:
            logger.error("Failed to create conversation: %s", str(exc))
            raise

    @staticmethod
    def update_last_message(conversation_id: str, content: str) -> None:
        """Denormalize the last message preview into the conversation row."""
        Conversation.objects.filter(id=conversation_id).update(
            last_message=content[:200],  # Truncate for preview
            last_message_at=timezone.now(),
            updated_at=timezone.now(),
        )

    @staticmethod
    def set_archived(conversation_id: str, archived: bool) -> bool:
        """Toggle the archived state. Returns True if updated."""
        updated = Conversation.objects.filter(id=conversation_id).update(
            is_archived=archived
        )
        return bool(updated)

    @staticmethod
    def set_pinned(conversation_id: str, pinned: bool) -> bool:
        """Toggle the pinned state."""
        updated = Conversation.objects.filter(id=conversation_id).update(
            is_pinned=pinned
        )
        return bool(updated)

    @staticmethod
    def set_blocked(
        conversation_id: str, blocked: bool, blocked_by: Optional[str] = None
    ) -> bool:
        """Block or unblock a conversation."""
        updated = Conversation.objects.filter(id=conversation_id).update(
            is_blocked=blocked,
            blocked_by=uuid.UUID(str(blocked_by)) if blocked and blocked_by else None,
        )
        return bool(updated)

    @staticmethod
    def delete(conversation_id: str) -> bool:
        """Hard delete a conversation and all its messages (CASCADE)."""
        deleted_count, _ = Conversation.objects.filter(id=conversation_id).delete()
        return bool(deleted_count)
