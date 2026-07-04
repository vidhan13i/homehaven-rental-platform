import urllib.parse
from channels.middleware import BaseMiddleware
import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket Middleware for authenticating via JWT.
    Extracts the token from the query string (e.g. ?token=...)
    and validates it against JWT_SECRET_KEY.
    Injects user_id into the ASGI scope.
    """
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = urllib.parse.parse_qs(query_string)
        
        token = query_params.get("token", [None])[0]
        
        if token:
            try:
                decoded = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=["HS256"]
                )
                scope["user_id"] = decoded.get("user_id")
            except Exception:
                scope["user_id"] = None
        else:
            scope["user_id"] = None
            
        return await super().__call__(scope, receive, send)
