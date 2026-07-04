import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser


class DummyUser:
    """
    A lightweight, fake user object to satisfy DRF's request.user requirement
    without querying a real User model (since notification_service has none).
    """
    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True


class TrustedJWTAuthentication(BaseAuthentication):
    """
    Stateless JWT authentication.
    Validates token against JWT_SECRET_KEY but DOES NOT query a database
    User model. Inject a DummyUser so request.user.id works in views.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            decoded = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = decoded.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Invalid token payload: missing user_id")
            
            return (DummyUser(user_id), token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")
