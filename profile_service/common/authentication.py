import jwt
from rest_framework import authentication, exceptions
from django.conf import settings

class SimpleJWTUser:
    def __init__(self, user_id, email=None, username=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False

    def __str__(self):
        return f"{self.username or self.id}"

class TrustedJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return None
        except ValueError:
            return None

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Token is missing user identifier')

        user = SimpleJWTUser(
            user_id=user_id,
            email=payload.get('email'),
            username=payload.get('username')
        )
        return (user, token)
