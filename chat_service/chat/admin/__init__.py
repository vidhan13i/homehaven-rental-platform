"""
Django Admin registration for chat_service models.
Scoped to /admin/chat/ via config/urls.py.
"""

from django.contrib import admin
from chat.models import Conversation, Message, Presence


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "listing_id",
        "owner_id",
        "renter_id",
        "last_message",
        "last_message_at",
        "is_archived",
        "is_pinned",
        "is_blocked",
        "created_at",
    ]
    list_filter = ["is_archived", "is_pinned", "is_blocked"]
    search_fields = ["listing_id", "owner_id", "renter_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "conversation",
        "sender_id",
        "message_type",
        "is_deleted",
        "is_edited",
        "created_at",
    ]
    list_filter = ["message_type"]
    search_fields = ["content", "sender_id"]
    readonly_fields = [
        "id",
        "delivered_at",
        "seen_at",
        "edited_at",
        "deleted_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]

    def is_deleted(self, obj):
        return obj.is_deleted

    is_deleted.boolean = True

    def is_edited(self, obj):
        return obj.is_edited

    is_edited.boolean = True


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ["user_id", "online", "last_seen"]
    list_filter = ["online"]
    readonly_fields = ["user_id", "last_seen"]
