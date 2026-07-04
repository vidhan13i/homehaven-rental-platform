"""
Message model.

Represents a single message within a Conversation.

Design decisions:
  - sender_id: UUID (cross-service reference, not a FK to auth_service)
  - reply_to: self-referential FK — allows "reply to message" feature
  - message_type: TextChoices enum for extensibility (text, image, pdf, doc, system)
  - attachment: URL string — in production this would reference an S3/CDN URL
  - deleted_at: soft delete — message content is cleared but the record remains
    so "This message was deleted" can be shown in the UI
  - edited_at: nullable — non-null means message was edited
  - delivered_at: set when the recipient's WebSocket receives the message
  - seen_at: set when the recipient explicitly reads (marks seen)
  - reactions: JSONField storing {emoji: [user_id, ...]} — flexible, no separate table
  - starred_by: JSONField [user_id, ...] — who has starred this message
  - forwarded_from: reference to original message UUID if forwarded
"""
import uuid
from django.db import models
from django.utils import timezone
from .base import ChatBaseModel
from .conversation import Conversation


class Message(ChatBaseModel):
    """A single message within a conversation."""

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        DOCUMENT = "document", "Document"
        SYSTEM = "system", "System"  # e.g., "Conversation started"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    # sender_id: UUID reference to auth_service user — not a FK
    sender_id = models.UUIDField(db_index=True)

    content = models.TextField(blank=True, default="")
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )

    # Optional file attachment — stores a URL (S3/CDN/local path)
    attachment = models.CharField(max_length=1024, blank=True, null=True)
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    attachment_size = models.PositiveBigIntegerField(null=True, blank=True)  # bytes

    # Threaded reply
    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies",
    )

    # Forward chain: UUID of the original message if this is a forward
    forwarded_from = models.UUIDField(null=True, blank=True)

    # Delivery/read receipts
    delivered_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)

    # Edit / soft delete
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Reactions: {"👍": ["uuid1", "uuid2"], "❤️": ["uuid3"]}
    reactions = models.JSONField(default=dict, blank=True)

    # Starred by: ["uuid1", "uuid2", ...]
    starred_by = models.JSONField(default=list, blank=True)

    class Meta:
        app_label = "chat"
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "deleted_at"]),
            models.Index(fields=["sender_id"]),
            models.Index(fields=["seen_at"]),
        ]

    def __str__(self) -> str:
        return f"Message({self.id}) in Conversation({self.conversation_id})"

    @property
    def is_deleted(self) -> bool:
        """Return True if this message has been soft-deleted."""
        return self.deleted_at is not None

    @property
    def is_edited(self) -> bool:
        """Return True if this message has been edited."""
        return self.edited_at is not None

    @property
    def display_content(self) -> str:
        """Content shown in the UI — redacted if deleted."""
        if self.is_deleted:
            return ""
        return self.content

    def soft_delete(self) -> None:
        """Soft-delete: clears content, sets deleted_at, preserves the record."""
        self.content = ""
        self.attachment = None
        self.deleted_at = timezone.now()
        self.save(update_fields=["content", "attachment", "deleted_at", "updated_at"])

    def mark_delivered(self) -> None:
        """Mark as delivered (called when recipient's WebSocket receives it)."""
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=["delivered_at", "updated_at"])

    def mark_seen(self) -> None:
        """Mark as seen by the recipient."""
        if not self.seen_at:
            self.seen_at = timezone.now()
            # Also set delivered if not already set
            if not self.delivered_at:
                self.delivered_at = self.seen_at
            self.save(update_fields=["delivered_at", "seen_at", "updated_at"])
