"""
Message Service.

Business logic for all message operations.
Called by both the WebSocket consumer and REST API views.
Coordinates: validation → rate limiting → sanitization → repository → notifications.
"""
import logging
from typing import Optional

from asgiref.sync import sync_to_async

from chat.models import Message, Conversation
from chat.repositories import ConversationRepository, MessageRepository
from chat.services.permission_service import PermissionService
from chat.utils.rate_limiter import MessageRateLimiter
from chat.utils.sanitizer import sanitize_message_content, validate_message_content

logger = logging.getLogger("chat.services.message")

# Module-level rate limiter instance (reuses Redis connection)
_rate_limiter = MessageRateLimiter()


class MessageService:
    """Business logic for message creation, editing, deletion, and reactions."""

    @staticmethod
    def send_message(
        conversation: Conversation,
        sender_id: str,
        content: str,
        message_type: str = "text",
        attachment: str = None,
        attachment_name: str = None,
        attachment_size: int = None,
        reply_to_id: str = None,
    ) -> tuple[Optional[Message], Optional[str]]:
        """
        Send a message in a conversation.

        Steps:
          1. Permission check (sender must be participant, conversation not blocked)
          2. Rate limiting (sliding window)
          3. Content validation and sanitization
          4. Persist to DB
          5. Update conversation last_message (denormalized)
          6. Queue offline notification if recipient is offline

        Returns (message, error_string) — error_string is None on success.
        """
        # 1. Permission
        allowed, reason = PermissionService.can_send_message(
            str(sender_id), conversation
        )
        if not allowed:
            logger.warning(
                "Message send denied for user %s in conversation %s: %s",
                sender_id, conversation.id, reason,
            )
            return None, reason

        # 2. Rate limit
        if not _rate_limiter.is_allowed(str(sender_id)):
            return None, "Rate limit exceeded. Please slow down."

        # 3. Sanitize + validate (for text messages)
        if message_type == "text":
            content = sanitize_message_content(content)
            error = validate_message_content(content)
            if error:
                return None, error
        elif not content and not attachment:
            return None, "Message must have content or an attachment"

        # 4. Persist
        try:
            message = MessageRepository.create(
                conversation_id=str(conversation.id),
                sender_id=str(sender_id),
                content=content,
                message_type=message_type,
                attachment=attachment,
                attachment_name=attachment_name,
                attachment_size=attachment_size,
                reply_to_id=reply_to_id,
            )
        except Exception as exc:
            logger.error(
                "Failed to persist message in conversation %s: %s",
                conversation.id, str(exc),
            )
            return None, "Failed to save message. Please try again."

        # 5. Update denormalized last_message on conversation
        preview = content[:200] if content else f"[{message_type}]"
        ConversationRepository.update_last_message(
            str(conversation.id), preview
        )

        logger.info(
            "Message %s sent in conversation %s by user %s",
            message.id, conversation.id, sender_id,
        )

        return message, None

    @staticmethod
    def edit_message(
        message_id: str, user_id: str, new_content: str
    ) -> tuple[Optional[Message], Optional[str]]:
        """Edit a message's text content. Only the sender can edit."""
        message = MessageRepository.get_by_id(message_id)
        if not message:
            return None, "Message not found"

        if message.is_deleted:
            return None, "Cannot edit a deleted message"

        if not PermissionService.can_modify_message(user_id, str(message.sender_id)):
            return None, "You can only edit your own messages"

        new_content = sanitize_message_content(new_content)
        error = validate_message_content(new_content)
        if error:
            return None, error

        updated = MessageRepository.edit(message_id, new_content)
        if updated:
            logger.info("Message %s edited by user %s", message_id, user_id)
        return updated, None

    @staticmethod
    def delete_message(
        message_id: str, user_id: str
    ) -> tuple[bool, Optional[str]]:
        """Soft-delete a message. Only the sender can delete."""
        message = MessageRepository.get_by_id(message_id)
        if not message:
            return False, "Message not found"

        if not PermissionService.can_modify_message(user_id, str(message.sender_id)):
            return False, "You can only delete your own messages"

        success = MessageRepository.soft_delete(message_id)
        if success:
            logger.info("Message %s soft-deleted by user %s", message_id, user_id)
        return success, None

    @staticmethod
    def mark_seen(conversation_id: str, user_id: str) -> int:
        """Mark all unread messages in a conversation as seen. Returns count."""
        count = MessageRepository.mark_all_seen_in_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        logger.debug(
            "Marked %d messages as seen in conversation %s by user %s",
            count, conversation_id, user_id,
        )
        return count

    @staticmethod
    def get_unread_count(conversation_id: str, user_id: str) -> int:
        """Return the number of unread messages for user_id in a conversation."""
        return MessageRepository.get_unread_count(conversation_id, user_id)

    @staticmethod
    def add_reaction(
        message_id: str, user_id: str, emoji: str
    ) -> tuple[Optional[Message], Optional[str]]:
        """Toggle a reaction on a message. Returns (message, error)."""
        if not emoji or len(emoji) > 10:
            return None, "Invalid emoji"

        message = MessageRepository.get_by_id(message_id)
        if not message:
            return None, "Message not found"

        updated = MessageRepository.add_reaction(message_id, user_id, emoji)
        return updated, None

    @staticmethod
    def toggle_star(
        message_id: str, user_id: str
    ) -> tuple[Optional[Message], Optional[str]]:
        """Star or unstar a message."""
        updated = MessageRepository.toggle_star(message_id, user_id)
        if not updated:
            return None, "Message not found"
        return updated, None

    @staticmethod
    def search_messages(
        conversation_id: str, query: str, user_id: str
    ):
        """Search messages in a conversation. User must be a participant."""
        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation or not conversation.is_participant(user_id):
            return []
        return MessageRepository.search(conversation_id, query)

    # ── Async wrappers for the WebSocket consumer ─────────────────────────────

    @staticmethod
    async def async_send_message(
        conversation: Conversation,
        sender_id: str,
        content: str,
        message_type: str = "text",
        attachment: str = None,
        reply_to_id: str = None,
    ) -> tuple[Optional[Message], Optional[str]]:
        """Async: send a message (wraps sync method)."""
        return await sync_to_async(MessageService.send_message)(
            conversation=conversation,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            attachment=attachment,
            reply_to_id=reply_to_id,
        )

    @staticmethod
    async def async_mark_seen(conversation_id: str, user_id: str) -> int:
        """Async: mark all messages seen in conversation."""
        return await sync_to_async(MessageService.mark_seen)(
            conversation_id, user_id
        )
