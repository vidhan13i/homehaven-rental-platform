"""
Serializers for chat_service REST API.
"""
from rest_framework import serializers
from chat.models import Conversation, Message, Presence


# ─── Message Serializers ──────────────────────────────────────────────────────

class ReplyToSerializer(serializers.ModelSerializer):
    """Minimal serializer for the replied-to message (nested in MessageSerializer)."""

    class Meta:
        model = Message
        fields = [
            "id", "sender_id", "content", "message_type",
            "is_deleted", "created_at",
        ]
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Full message serializer for detail and WebSocket payloads."""

    reply_to = ReplyToSerializer(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    is_edited = serializers.BooleanField(read_only=True)
    display_content = serializers.CharField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender_id",
            "content",
            "display_content",
            "message_type",
            "attachment",
            "attachment_name",
            "attachment_size",
            "reply_to",
            "reply_to_id",
            "forwarded_from",
            "is_deleted",
            "is_edited",
            "reactions",
            "starred_by",
            "delivered_at",
            "seen_at",
            "edited_at",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "conversation", "sender_id", "is_deleted",
            "is_edited", "reactions", "starred_by",
            "delivered_at", "seen_at", "edited_at", "deleted_at",
            "created_at", "updated_at",
        ]


class MessageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for message list (omits nested reply object)."""

    is_deleted = serializers.BooleanField(read_only=True)
    display_content = serializers.CharField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "sender_id",
            "display_content", "message_type", "attachment",
            "is_deleted", "is_edited", "reactions",
            "delivered_at", "seen_at", "created_at",
        ]
        read_only_fields = fields


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message via REST API."""

    class Meta:
        model = Message
        fields = [
            "content",
            "message_type",
            "attachment",
            "attachment_name",
            "attachment_size",
            "reply_to",
        ]

    def validate_message_type(self, value: str) -> str:
        from chat.utils.sanitizer import validate_message_type
        if not validate_message_type(value):
            raise serializers.ValidationError(f"Invalid message type: {value}")
        return value

    def validate_content(self, value: str) -> str:
        from chat.utils.sanitizer import sanitize_message_content
        return sanitize_message_content(value)


class MessageEditSerializer(serializers.Serializer):
    """Serializer for editing a message's content."""

    content = serializers.CharField(max_length=4000)

    def validate_content(self, value: str) -> str:
        from chat.utils.sanitizer import sanitize_message_content, validate_message_content
        sanitized = sanitize_message_content(value)
        error = validate_message_content(sanitized)
        if error:
            raise serializers.ValidationError(error)
        return sanitized


class ReactionSerializer(serializers.Serializer):
    """Serializer for adding/removing a reaction."""

    emoji = serializers.CharField(max_length=10)


# ─── Conversation Serializers ─────────────────────────────────────────────────

class ConversationSerializer(serializers.ModelSerializer):
    """Full conversation serializer."""

    class Meta:
        model = Conversation
        fields = [
            "id",
            "listing_id",
            "owner_id",
            "renter_id",
            "last_message",
            "last_message_at",
            "is_archived",
            "is_pinned",
            "is_blocked",
            "blocked_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "owner_id", "renter_id",
            "last_message", "last_message_at",
            "created_at", "updated_at",
        ]


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for conversation list with unread count."""

    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "listing_id",
            "owner_id",
            "renter_id",
            "last_message",
            "last_message_at",
            "is_archived",
            "is_pinned",
            "is_blocked",
            "unread_count",
            "created_at",
        ]

    def get_unread_count(self, obj: Conversation) -> int:
        request = self.context.get("request")
        if not request or not request.user:
            return 0
        from chat.repositories import MessageRepository
        return MessageRepository.get_unread_count(
            conversation_id=str(obj.id),
            user_id=str(request.user.id),
        )


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer for creating a new conversation."""

    listing_id = serializers.UUIDField()
    owner_id = serializers.UUIDField()
    renter_id = serializers.UUIDField()

    def validate(self, data: dict) -> dict:
        if data["owner_id"] == data["renter_id"]:
            raise serializers.ValidationError(
                "owner_id and renter_id cannot be the same user"
            )
        return data


# ─── Presence Serializer ──────────────────────────────────────────────────────

class PresenceSerializer(serializers.ModelSerializer):
    """Serializer for the Presence model."""

    class Meta:
        model = Presence
        fields = ["user_id", "online", "last_seen"]
