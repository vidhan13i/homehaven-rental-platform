"""
Message Repository.

Encapsulates all database access for Message objects.
"""

import logging
import uuid
from typing import Optional

from django.db.models import QuerySet
from django.utils import timezone

from chat.models import Message

logger = logging.getLogger("chat.repositories.message")


class MessageRepository:
    """Data access layer for Message objects."""

    @staticmethod
    def get_by_id(message_id: str) -> Optional[Message]:
        """Fetch a single message by UUID."""
        try:
            return Message.objects.select_related("conversation", "reply_to").get(
                id=message_id
            )
        except (Message.DoesNotExist, ValueError):
            return None

    @staticmethod
    def get_for_conversation(
        conversation_id: str,
        include_deleted: bool = False,
    ) -> QuerySet:
        """
        Fetch all messages for a conversation, ordered oldest-first.
        Excludes soft-deleted messages by default.
        """
        qs = (
            Message.objects.filter(conversation_id=conversation_id)
            .select_related("reply_to")
            .order_by("created_at")
        )

        if not include_deleted:
            qs = qs.filter(deleted_at__isnull=True)

        return qs

    @staticmethod
    def create(
        conversation_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
        attachment: str = None,
        attachment_name: str = None,
        attachment_size: int = None,
        reply_to_id: str = None,
        forwarded_from: str = None,
    ) -> Message:
        """Create and persist a new message."""
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(
                    id=reply_to_id, conversation_id=conversation_id
                )
            except Message.DoesNotExist:
                logger.warning("reply_to_id %s not found", reply_to_id)

        msg = Message.objects.create(
            conversation_id=uuid.UUID(str(conversation_id)),
            sender_id=uuid.UUID(str(sender_id)),
            content=content,
            message_type=message_type,
            attachment=attachment,
            attachment_name=attachment_name,
            attachment_size=attachment_size,
            reply_to=reply_to,
            forwarded_from=uuid.UUID(str(forwarded_from)) if forwarded_from else None,
        )
        return msg

    @staticmethod
    def edit(message_id: str, new_content: str) -> Optional[Message]:
        """Edit a message's content. Returns the updated message or None."""
        updated = Message.objects.filter(
            id=message_id,
            deleted_at__isnull=True,  # Cannot edit deleted messages
        ).update(
            content=new_content,
            edited_at=timezone.now(),
            updated_at=timezone.now(),
        )
        if updated:
            return MessageRepository.get_by_id(message_id)
        return None

    @staticmethod
    def soft_delete(message_id: str) -> bool:
        """Soft-delete a message: clears content, preserves record."""
        updated = Message.objects.filter(
            id=message_id,
            deleted_at__isnull=True,
        ).update(
            content="",
            attachment=None,
            deleted_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return bool(updated)

    @staticmethod
    def mark_delivered(message_id: str) -> None:
        """Mark a message as delivered to the recipient."""
        Message.objects.filter(id=message_id, delivered_at__isnull=True).update(
            delivered_at=timezone.now(), updated_at=timezone.now()
        )

    @staticmethod
    def mark_seen(message_id: str) -> None:
        """Mark a message as seen by the recipient."""
        Message.objects.filter(id=message_id, seen_at__isnull=True).update(
            seen_at=timezone.now(),
            delivered_at=timezone.now(),
            updated_at=timezone.now(),
        )

    @staticmethod
    def mark_all_seen_in_conversation(conversation_id: str, user_id: str) -> int:
        """
        Mark all messages in a conversation as seen by a specific user
        (i.e., messages NOT sent by that user that haven't been seen yet).
        Returns the count of updated messages.
        """
        updated = (
            Message.objects.filter(
                conversation_id=conversation_id,
                seen_at__isnull=True,
                deleted_at__isnull=True,
            )
            .exclude(sender_id=uuid.UUID(str(user_id)))
            .update(
                seen_at=timezone.now(),
                delivered_at=timezone.now(),
                updated_at=timezone.now(),
            )
        )
        return updated

    @staticmethod
    def get_unread_count(conversation_id: str, user_id: str) -> int:
        """Count messages not yet seen by user_id in a conversation."""
        return (
            Message.objects.filter(
                conversation_id=conversation_id,
                seen_at__isnull=True,
                deleted_at__isnull=True,
            )
            .exclude(sender_id=uuid.UUID(str(user_id)))
            .count()
        )

    @staticmethod
    def add_reaction(message_id: str, user_id: str, emoji: str) -> Optional[Message]:
        """
        Toggle a reaction emoji on a message.
        If the user has already reacted with this emoji, remove it.
        Returns the updated message.
        """
        msg = MessageRepository.get_by_id(message_id)
        if not msg or msg.is_deleted:
            return None

        reactions: dict = msg.reactions or {}
        user_list: list = reactions.get(emoji, [])

        if user_id in user_list:
            user_list.remove(user_id)  # Toggle off
        else:
            user_list.append(user_id)  # Toggle on

        if user_list:
            reactions[emoji] = user_list
        else:
            reactions.pop(emoji, None)  # Remove empty emoji key

        msg.reactions = reactions
        msg.save(update_fields=["reactions", "updated_at"])
        return msg

    @staticmethod
    def toggle_star(message_id: str, user_id: str) -> Optional[Message]:
        """Star or unstar a message for a user."""
        msg = MessageRepository.get_by_id(message_id)
        if not msg:
            return None

        starred: list = msg.starred_by or []
        if user_id in starred:
            starred.remove(user_id)
        else:
            starred.append(user_id)

        msg.starred_by = starred
        msg.save(update_fields=["starred_by", "updated_at"])
        return msg

    @staticmethod
    def search(conversation_id: str, query: str) -> QuerySet:
        """Full-text search across non-deleted messages in a conversation."""
        return (
            Message.objects.filter(
                conversation_id=conversation_id,
                deleted_at__isnull=True,
            )
            .filter(content__icontains=query)
            .order_by("-created_at")
        )
