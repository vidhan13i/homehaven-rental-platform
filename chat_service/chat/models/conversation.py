"""
Conversation model.

A Conversation is a thread between exactly two parties:
  - owner_id  : the listing owner (UUID from auth_service)
  - renter_id : the applicant/renter (UUID from auth_service)

It is scoped to a specific listing (listing_id from listings_service).

Design decisions:
  - owner_id, renter_id, listing_id are UUID fields (not FKs) because this service
    does NOT directly access auth_service or listings_service databases.
    The IDs are stored as references validated via HTTP at conversation creation time.
  - unique_together on (listing_id, owner_id, renter_id) prevents duplicate conversations.
  - last_message / last_message_at are denormalized for O(1) conversation list rendering
    (avoids a JOIN or subquery on the messages table for every conversation row).
  - is_pinned per-participant would require a separate PinRecord model; here we use
    a single boolean that represents the owner's pin state. A production system
    would use a separate UserConversationState model for per-user pin/archive state.
"""

import uuid
from django.db import models
from .base import ChatBaseModel


class Conversation(ChatBaseModel):
    """A messaging thread between a listing owner and a renter."""

    # Foreign references — stored as UUIDs, resolved via inter-service HTTP calls
    listing_id = models.UUIDField(db_index=True)
    owner_id = models.UUIDField(db_index=True)  # Listing owner
    renter_id = models.UUIDField(db_index=True)  # Applicant / tenant

    # Denormalized last-message fields for fast conversation list rendering
    last_message = models.TextField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Lifecycle flags
    is_archived = models.BooleanField(default=False, db_index=True)
    is_pinned = models.BooleanField(default=False, db_index=True)
    is_blocked = models.BooleanField(default=False, db_index=True)
    blocked_by = models.UUIDField(null=True, blank=True)  # user_id who blocked

    class Meta:
        app_label = "chat"
        db_table = "chat_conversations"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["owner_id", "is_archived"]),
            models.Index(fields=["renter_id", "is_archived"]),
            models.Index(fields=["listing_id", "owner_id", "renter_id"]),
        ]
        # Prevents two conversations for the same listing between the same two users
        constraints = [
            models.UniqueConstraint(
                fields=["listing_id", "owner_id", "renter_id"],
                name="unique_conversation_per_listing_pair",
            )
        ]

    def __str__(self) -> str:
        return f"Conversation({self.id}) listing={self.listing_id}"

    def get_other_participant(self, user_id: str) -> str | None:
        """Return the ID of the other participant given one participant's ID."""
        uid = uuid.UUID(str(user_id))
        if uid == self.owner_id:
            return str(self.renter_id)
        if uid == self.renter_id:
            return str(self.owner_id)
        return None

    def is_participant(self, user_id: str) -> bool:
        """Return True if user_id is either owner or renter in this conversation."""
        uid = uuid.UUID(str(user_id))
        return uid in (self.owner_id, self.renter_id)
