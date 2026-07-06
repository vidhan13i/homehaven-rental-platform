"""
REST URL configuration for chat_service.

All URLs are prefixed with /api/chat/ (applied in config/urls.py).

Endpoint map:
 CONVERSATIONS
 GET    /api/chat/conversations/                  → list (paginated)
 POST   /api/chat/conversations/                  → create
 GET    /api/chat/conversations/<id>/             → detail
 DELETE /api/chat/conversations/<id>/             → delete (archive)
 POST   /api/chat/conversations/<id>/archive/     → archive toggle
 POST   /api/chat/conversations/<id>/pin/         → pin toggle
 POST   /api/chat/conversations/<id>/block/       → block conversation
 POST   /api/chat/conversations/<id>/unblock/     → unblock
 POST   /api/chat/conversations/<id>/mark_read/   → mark all messages read
 GET    /api/chat/conversations/<id>/unread_count/→ unread count for this convo

 MESSAGES
 GET    /api/chat/messages/?conversation=<id>     → list messages (paginated)
 POST   /api/chat/messages/                       → send a message
 GET    /api/chat/messages/<id>/                  → message detail
 PATCH  /api/chat/messages/<id>/                  → edit message
 DELETE /api/chat/messages/<id>/                  → soft delete
 POST   /api/chat/messages/<id>/react/            → add/remove reaction
 POST   /api/chat/messages/<id>/forward/          → forward to another conversation
 POST   /api/chat/messages/<id>/star/             → star/unstar message
 GET    /api/chat/messages/search/?q=<query>      → full-text search

 PRESENCE
 GET    /api/chat/presence/<user_id>/             → get online status + last_seen

 HEALTH
 GET    /api/chat/health/                         → service health check
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from chat.api.views import (
    ConversationViewSet,
    MessageViewSet,
    PresenceView,
    HealthView,
)

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
    path("presence/<str:user_id>/", PresenceView.as_view(), name="presence"),
    path("health/", HealthView.as_view(), name="chat-health"),
    path("api-auth/", include("rest_framework.urls")),
]
