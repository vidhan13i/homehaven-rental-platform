"""
Unit tests for JWT authentication (HTTP and WebSocket).
"""
import uuid
import time

import jwt
from django.test import TestCase, RequestFactory, override_settings
from rest_framework.exceptions import AuthenticationFailed

from chat.authentication.http import TrustedJWTAuthentication, SimpleJWTUser
from chat.authentication.websocket import (
    authenticate_websocket_token,
    extract_token_from_scope,
)

TEST_JWT_SECRET = "test-secret-key-for-unit-tests"
TEST_USER_ID = str(uuid.uuid4())
TEST_USER_EMAIL = "test@haven.local"
TEST_USERNAME = "testuser"


def _make_token(
    user_id: str = TEST_USER_ID,
    email: str = TEST_USER_EMAIL,
    username: str = TEST_USERNAME,
    expired: bool = False,
    missing_user_id: bool = False,
    secret: str = TEST_JWT_SECRET,
) -> str:
    """Helper to generate test JWT tokens."""
    payload = {
        "email": email,
        "username": username,
    }
    if not missing_user_id:
        payload["user_id"] = user_id

    if expired:
        payload["exp"] = int(time.time()) - 3600  # 1 hour ago
    else:
        payload["exp"] = int(time.time()) + 3600  # 1 hour from now

    return jwt.encode(payload, secret, algorithm="HS256")


@override_settings(JWT_SECRET_KEY=TEST_JWT_SECRET)
class TrustedJWTAuthenticationTest(TestCase):
    """Tests for HTTP JWT authentication."""

    def setUp(self):
        self.auth = TrustedJWTAuthentication()
        self.factory = RequestFactory()

    def _request_with_token(self, token: str):
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return request

    def test_valid_token_authenticates(self):
        token = _make_token()
        request = self._request_with_token(token)
        user, returned_token = self.auth.authenticate(request)

        self.assertIsInstance(user, SimpleJWTUser)
        self.assertEqual(str(user.id), TEST_USER_ID)
        self.assertEqual(user.email, TEST_USER_EMAIL)
        self.assertEqual(user.username, TEST_USERNAME)
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)

    def test_no_authorization_header_returns_none(self):
        request = self.factory.get("/")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_expired_token_raises_authentication_failed(self):
        token = _make_token(expired=True)
        request = self._request_with_token(token)
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("expired", str(ctx.exception).lower())

    def test_invalid_token_raises_authentication_failed(self):
        request = self._request_with_token("not.a.valid.jwt.token")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_wrong_secret_raises_authentication_failed(self):
        token = _make_token(secret="wrong-secret")
        request = self._request_with_token(token)
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_token_missing_user_id_raises_authentication_failed(self):
        token = _make_token(missing_user_id=True)
        request = self._request_with_token(token)
        with self.assertRaises(AuthenticationFailed) as ctx:
            self.auth.authenticate(request)
        self.assertIn("user identifier", str(ctx.exception))

    def test_malformed_authorization_header_returns_none(self):
        """Only token, no 'Bearer' prefix."""
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = "justtoken"
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_wrong_scheme_returns_none(self):
        """Token with 'Token' scheme (not 'Bearer') should return None."""
        token = _make_token()
        request = self.factory.get("/")
        request.META["HTTP_AUTHORIZATION"] = f"Token {token}"
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_header_returns_bearer(self):
        request = self.factory.get("/")
        self.assertEqual(self.auth.authenticate_header(request), "Bearer")


@override_settings(JWT_SECRET_KEY=TEST_JWT_SECRET)
class WebSocketAuthenticationTest(TestCase):
    """Tests for WebSocket JWT authentication."""

    def test_valid_token_returns_user(self):
        token = _make_token()
        user = authenticate_websocket_token(token)
        self.assertIsNotNone(user)
        self.assertIsInstance(user, SimpleJWTUser)
        self.assertEqual(str(user.id), TEST_USER_ID)

    def test_empty_token_returns_none(self):
        result = authenticate_websocket_token("")
        self.assertIsNone(result)

    def test_none_token_returns_none(self):
        result = authenticate_websocket_token(None)
        self.assertIsNone(result)

    def test_expired_token_returns_none(self):
        token = _make_token(expired=True)
        result = authenticate_websocket_token(token)
        self.assertIsNone(result)

    def test_invalid_token_returns_none(self):
        result = authenticate_websocket_token("garbage.token.here")
        self.assertIsNone(result)

    def test_extract_token_from_scope(self):
        scope = {"query_string": b"token=my_jwt_token&other=value"}
        token = extract_token_from_scope(scope)
        self.assertEqual(token, "my_jwt_token")

    def test_extract_token_missing_returns_empty(self):
        scope = {"query_string": b"other=value"}
        token = extract_token_from_scope(scope)
        self.assertEqual(token, "")

    def test_extract_token_empty_query_string(self):
        scope = {"query_string": b""}
        token = extract_token_from_scope(scope)
        self.assertEqual(token, "")
