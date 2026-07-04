"""
Filters for chat_service REST API.
"""

import django_filters
from chat.models import Conversation, Message


class ConversationFilter(django_filters.FilterSet):
    is_archived = django_filters.BooleanFilter(field_name="is_archived")
    is_pinned = django_filters.BooleanFilter(field_name="is_pinned")
    listing_id = django_filters.UUIDFilter(field_name="listing_id")

    class Meta:
        model = Conversation
        fields = ["is_archived", "is_pinned", "listing_id"]


class MessageFilter(django_filters.FilterSet):
    conversation = django_filters.UUIDFilter(field_name="conversation__id")
    message_type = django_filters.CharFilter(field_name="message_type")
    sender_id = django_filters.UUIDFilter(field_name="sender_id")

    class Meta:
        model = Message
        fields = ["conversation", "message_type", "sender_id"]
