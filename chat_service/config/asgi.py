"""
ASGI config for chat_service.

This is the main ASGI entry point that Daphne loads.

How it works:
  1. Django's get_asgi_application() handles all HTTP requests (REST API, admin).
  2. channels.routing.ProtocolTypeRouter inspects the protocol:
     - "http"      → standard Django HTTP stack
     - "websocket" → Django Channels WebSocket consumer stack

The WebSocket stack adds:
  - AllowedHostsOriginValidator: Validates the Origin header against ALLOWED_HOSTS
    (prevents WebSocket connections from unauthorized origins — CSRF equivalent for WS)
  - AuthMiddlewareStack: NOT used here because we do JWT auth inside the consumer.
    We don't want Django session/cookie auth for WebSockets in a microservice.
  - URLRouter: Routes WebSocket connections to the correct consumer by URL pattern.
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # HTTP → standard Django ASGI handler (REST API, admin, health check)
        "http": get_asgi_application(),
        # WebSocket → Django Channels consumer
        # AllowedHostsOriginValidator checks the Origin header.
        # In dev (DEBUG=True), all origins are allowed automatically.
        "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns)),
    }
)
