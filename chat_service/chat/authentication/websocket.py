"""
WebSocket JWT Authentication for Django Channels consumers.

WebSocket connections cannot reliably send Authorization headers after the
initial HTTP upgrade (browser WebSocket API does not support custom headers).

Two common solutions:
  1. Query parameter: ?token=<jwt>  ← We use this approach
  2. First-message auth: client sends token as first WebSocket message

We use approach 1 (query parameter) because:
  - It's simpler and widely used in production (Pusher, Ably, etc.)
  - The token is only transmitted during the HTTP upgrade handshake (TLS encrypted)
  - The token is validated BEFORE the WebSocket is accepted (in websocket_connect)

Usage in consumer:
    from chat.authentication.websocket import authenticate_websocket_token

    async def websocket_connect(self, message):
        token = self.scope["query_string"].decode().split("token=")[-1]
        user = await authenticate_websocket_token(token)
        if user is None:
            await self.close(code=4001)  # 4001: Unauthorized
            return
        self.user = user
        await self.accept()
"""
import logging
import urllib.parse
import jwt
from django.conf import settings
from .http import SimpleJWTUser

logger = logging.getLogger("chat.authentication")

# Custom WebSocket close codes (4000-4999 are application-defined)
WS_CLOSE_CODE_UNAUTHORIZED = 4001
WS_CLOSE_CODE_FORBIDDEN = 4003
WS_CLOSE_CODE_EXPIRED = 4002


def authenticate_websocket_token(token: str) -> SimpleJWTUser | None:
    """
    Decode and validate a JWT token from a WebSocket query parameter.

    Returns a SimpleJWTUser on success, None on any failure.
    Callers must close the WebSocket with code 4001 if this returns None.

    This is intentionally synchronous — it's called with database_sync_to_async
    or in sync context. JWT decoding itself is CPU-bound and non-blocking.
    """
    if not token:
        logger.warning("WebSocket auth failed: no token provided")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth failed: token expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("WebSocket auth failed: %s", str(exc))
        return None

    user_id = payload.get("user_id")
    if not user_id:
        logger.warning("WebSocket auth failed: missing user_id claim")
        return None

    user = SimpleJWTUser(
        user_id=str(user_id),
        email=payload.get("email"),
        username=payload.get("username"),
    )
    logger.debug("WebSocket authenticated user %s", user_id)
    return user


def extract_token_from_scope(scope: dict) -> str:
    """
    Extract the JWT token from the WebSocket connection scope.

    Parses the query string for the 'token' parameter.
    Example: /ws/chat/<id>/?token=eyJ...  →  "eyJ..."
    """
    query_string = scope.get("query_string", b"").decode("utf-8")
    params = urllib.parse.parse_qs(query_string)
    token_list = params.get("token", [])
    return token_list[0] if token_list else ""
