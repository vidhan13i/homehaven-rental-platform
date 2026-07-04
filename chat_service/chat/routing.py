"""
WebSocket URL routing for chat_service.

This module defines the WebSocket URL patterns consumed by the ASGI router
in config/asgi.py.

URL format: /ws/chat/<conversation_id>/
  - conversation_id: UUID of the Conversation model
  - Every WebSocket connection joins exactly ONE conversation group:
      group name = "chat_{conversation_id}"

The JWT token is passed as a query parameter:
  wss://host/ws/chat/<uuid>/?token=<jwt_access_token>
"""

from django.urls import re_path
from chat.consumers.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/chat/(?P<conversation_id>[0-9a-f-]{36})/$",
        ChatConsumer.as_asgi(),
    ),
]
