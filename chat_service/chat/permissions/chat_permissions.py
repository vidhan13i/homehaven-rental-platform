"""
DRF Permission classes for chat service REST endpoints.

IsConversationParticipant: Only the owner or renter may access a conversation.
IsMessageSender: Only the original sender may edit or delete a message.
"""
import logging
from rest_framework.permissions import BasePermission

logger = logging.getLogger("chat.permissions")


class IsConversationParticipant(BasePermission):
    """
    Allow access only if the authenticated user is a participant
    (owner_id or renter_id) in the Conversation object.

    Used on:
      - Conversation detail, update, delete views
      - Message list/create views (via conversation)
    """

    message = "You do not have permission to access this conversation."

    def has_object_permission(self, request, view, obj) -> bool:
        from chat.models import Conversation

        if isinstance(obj, Conversation):
            conversation = obj
        else:
            # obj is a Message — get its conversation
            conversation = obj.conversation

        user_id = str(request.user.id)
        is_participant = conversation.is_participant(user_id)

        if not is_participant:
            logger.warning(
                "Permission denied: user %s attempted to access conversation %s",
                user_id,
                conversation.id,
            )

        return is_participant


class IsMessageSender(BasePermission):
    """
    Allow edit/delete only if the authenticated user is the message sender.
    """

    message = "You can only edit or delete your own messages."

    def has_object_permission(self, request, view, obj) -> bool:
        from chat.models import Message

        if not isinstance(obj, Message):
            return False

        return str(obj.sender_id) == str(request.user.id)


class IsNotBlocked(BasePermission):
    """
    Deny access if the conversation is blocked.
    A blocked conversation disallows new messages.
    """

    message = "This conversation has been blocked."

    def has_object_permission(self, request, view, obj) -> bool:
        from chat.models import Conversation

        if isinstance(obj, Conversation):
            if obj.is_blocked:
                logger.info(
                    "Access denied: conversation %s is blocked by %s",
                    obj.id,
                    obj.blocked_by,
                )
                return False
        return True
