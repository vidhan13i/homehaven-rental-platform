"""
HTTP JWT Authentication for the chat service REST API.

This is a direct port of the TrustedJWTAuthentication pattern established in:
  - listings_service/common/authentication.py
  - profile_service/common/authentication.py
  - application_service/common/authentication.py

The pattern:
  1. Read Bearer token from Authorization header
  2. Decode with shared JWT_SECRET_KEY (HS256)
  3. Extract user_id, email, username claims
  4. Return (SimpleJWTUser, token) — no DB hit, fully stateless

SimpleJWTUser is a lightweight, non-ORM user object that satisfies
Django REST Framework's is_authenticated check.
"""
import logging
import jwt
from rest_framework import authentication, exceptions
from django.conf import settings

logger = logging.getLogger("chat.authentication")


class SimpleJWTUser:
    """
    Lightweight user object built from JWT claims.

    Not backed by any database model — stateless, microservice-safe.
    Satisfies DRF's is_authenticated contract.
    """

    def __init__(self, user_id: str, email: str = None, username: str = None):
        self.id = user_id
        self.pk = user_id  # DRF compatibility
        self.email = email
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False
        self.is_anonymous = False

    def __str__(self) -> str:
        return f"{self.username or self.id}"

    def __repr__(self) -> str:
        return f"SimpleJWTUser(id={self.id!r}, username={self.username!r})"


class TrustedJWTAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class for chat_service HTTP endpoints.

    Used in settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].
    Every authenticated REST endpoint automatically runs this before the view.
    """

    def authenticate(self, request) -> tuple[SimpleJWTUser, str] | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None  # Allow DRF to try other authentication backends

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        return self._decode_token(token)

    def _decode_token(self, token: str) -> tuple[SimpleJWTUser, str]:
        """Decode and validate the JWT. Raises AuthenticationFailed on any error."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            logger.warning("JWT authentication failed: token expired")
            raise exceptions.AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError as exc:
            logger.warning("JWT authentication failed: %s", str(exc))
            raise exceptions.AuthenticationFailed("Invalid token")

        user_id = payload.get("user_id")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token is missing user identifier")

        user = SimpleJWTUser(
            user_id=str(user_id),
            email=payload.get("email"),
            username=payload.get("username"),
        )
        logger.debug("Authenticated user %s via JWT", user_id)
        return (user, token)

    def authenticate_header(self, request) -> str:
        return "Bearer"
