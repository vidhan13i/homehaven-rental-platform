"""
API integration tests for chat_service REST endpoints.

Uses Django's test database (chat_db via database router).
Authenticates with a real JWT signed with the test secret.
"""

import uuid
import time
import jwt

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from chat.models import Conversation, Message

TEST_JWT_SECRET = "test-secret-key-for-api-tests"


def _make_jwt(
    user_id: str, username: str = "testuser", email: str = "t@test.com"
) -> str:
    """Generate a valid JWT for a test user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def _create_conversation(
    owner_id: str, renter_id: str, listing_id: str = None
) -> Conversation:
    """Helper to create a conversation directly in the test DB."""
    return Conversation.objects.using("chat").create(
        listing_id=uuid.UUID(str(listing_id or uuid.uuid4())),
        owner_id=uuid.UUID(str(owner_id)),
        renter_id=uuid.UUID(str(renter_id)),
    )


@override_settings(JWT_SECRET_KEY=TEST_JWT_SECRET)
class ConversationAPITest(TestCase):
    """Integration tests for ConversationViewSet."""

    databases = {"default", "chat"}

    def setUp(self):
        self.client = APIClient()
        self.owner_id = str(uuid.uuid4())
        self.renter_id = str(uuid.uuid4())
        self.third_party_id = str(uuid.uuid4())

        # Authenticate as owner
        token = _make_jwt(self.owner_id, username="owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_create_conversation_as_owner(self):
        """Owner can create a conversation for a listing they own."""
        listing_id = str(uuid.uuid4())
        response = self.client.post(
            "/api/chat/conversations/",
            {
                "listing_id": listing_id,
                "owner_id": self.owner_id,
                "renter_id": self.renter_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["owner_id"], self.owner_id)
        self.assertEqual(data["renter_id"], self.renter_id)

    def test_create_duplicate_conversation_returns_200(self):
        """Creating the same conversation twice returns HTTP 200 (not 201)."""
        listing_id = str(uuid.uuid4())
        payload = {
            "listing_id": listing_id,
            "owner_id": self.owner_id,
            "renter_id": self.renter_id,
        }
        r1 = self.client.post("/api/chat/conversations/", payload, format="json")
        r2 = self.client.post("/api/chat/conversations/", payload, format="json")

        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.json()["id"], r2.json()["id"])

    def test_create_self_conversation_rejected(self):
        """Cannot create a conversation where owner == renter."""
        response = self.client.post(
            "/api/chat/conversations/",
            {
                "listing_id": str(uuid.uuid4()),
                "owner_id": self.owner_id,
                "renter_id": self.owner_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_list_returns_only_user_conversations(self):
        """User only sees conversations they participate in."""
        # Own conversation
        _create_conversation(self.owner_id, self.renter_id)
        # Another conversation the owner is not part of
        _create_conversation(str(uuid.uuid4()), str(uuid.uuid4()))

        response = self.client.get("/api/chat/conversations/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_third_party_cannot_access_conversation(self):
        """A user who is not owner or renter gets 404."""
        conv = _create_conversation(self.owner_id, self.renter_id)

        # Switch to third-party auth
        token = _make_jwt(self.third_party_id, username="stranger")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(f"/api/chat/conversations/{conv.id}/")
        self.assertIn(response.status_code, [403, 404])

    def test_unauthenticated_request_rejected(self):
        """No JWT → 401 Unauthorized."""
        self.client.credentials()  # Clear credentials
        response = self.client.get("/api/chat/conversations/")
        self.assertEqual(response.status_code, 401)

    def test_archive_conversation(self):
        """Owner can archive a conversation."""
        conv = _create_conversation(self.owner_id, self.renter_id)
        response = self.client.post(f"/api/chat/conversations/{conv.id}/archive/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["archived"])

    def test_pin_conversation(self):
        """Owner can pin a conversation."""
        conv = _create_conversation(self.owner_id, self.renter_id)
        response = self.client.post(f"/api/chat/conversations/{conv.id}/pin/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["pinned"])


@override_settings(JWT_SECRET_KEY=TEST_JWT_SECRET)
class MessageAPITest(TestCase):
    """Integration tests for MessageViewSet."""

    databases = {"default", "chat"}

    def setUp(self):
        self.client = APIClient()
        self.owner_id = str(uuid.uuid4())
        self.renter_id = str(uuid.uuid4())

        self.conversation = _create_conversation(self.owner_id, self.renter_id)

        # Authenticate as owner
        token = _make_jwt(self.owner_id, username="owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _post_message(self, content: str = "Hello!", message_type: str = "text"):
        return self.client.post(
            "/api/chat/messages/",
            {
                "conversation": str(self.conversation.id),
                "content": content,
                "message_type": message_type,
            },
            format="json",
        )

    def test_send_message(self):
        """Can send a text message via REST API."""
        response = self._post_message("Hello, are you available?")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["content"], "Hello, are you available?")
        self.assertEqual(data["sender_id"], self.owner_id)
        self.assertEqual(data["message_type"], "text")

    def test_send_empty_message_rejected(self):
        """Empty content is rejected."""
        response = self._post_message(content="   ")
        self.assertEqual(response.status_code, 400)

    def test_send_html_is_stripped(self):
        """HTML injection is stripped from content."""
        response = self._post_message(content="<script>alert('xss')</script>Hello")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertNotIn("<script>", data["content"])

    def test_list_messages_requires_conversation(self):
        """Message list requires conversation query param."""
        response = self.client.get("/api/chat/messages/")
        # Returns empty (no conversation param → empty queryset)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

    def test_edit_own_message(self):
        """Sender can edit their own message."""
        r = self._post_message("Original content")
        message_id = r.json()["id"]

        edit_response = self.client.patch(
            f"/api/chat/messages/{message_id}/",
            {"content": "Edited content"},
            format="json",
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(edit_response.json()["content"], "Edited content")

    def test_delete_own_message(self):
        """Sender can soft-delete their own message."""
        r = self._post_message("To be deleted")
        message_id = r.json()["id"]

        delete_response = self.client.delete(f"/api/chat/messages/{message_id}/")
        self.assertEqual(delete_response.status_code, 204)

        # Message should still exist but marked deleted
        msg = Message.objects.using("chat").get(id=message_id)
        self.assertIsNotNone(msg.deleted_at)
        self.assertEqual(msg.content, "")

    def test_renter_cannot_edit_owners_message(self):
        """Renter cannot edit owner's message."""
        r = self._post_message("Owner's message")
        message_id = r.json()["id"]

        # Switch to renter auth
        renter_token = _make_jwt(self.renter_id, username="renter")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {renter_token}")

        edit_response = self.client.patch(
            f"/api/chat/messages/{message_id}/",
            {"content": "Hacked!"},
            format="json",
        )
        self.assertIn(edit_response.status_code, [403, 404])

    def test_react_to_message(self):
        """Can add a reaction to a message."""
        r = self._post_message("React to this")
        message_id = r.json()["id"]

        react_response = self.client.post(
            f"/api/chat/messages/{message_id}/react/",
            {"emoji": "👍"},
            format="json",
        )
        self.assertEqual(react_response.status_code, 200)
        reactions = react_response.json()["reactions"]
        self.assertIn("👍", reactions)
        self.assertIn(self.owner_id, reactions["👍"])

    def test_search_messages(self):
        """Can search messages by content."""
        self._post_message("Looking for apartments")
        self._post_message("This is a different topic")

        response = self.client.get(
            f"/api/chat/messages/search/?q=apartments&conversation={self.conversation.id}"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertIn("apartments", results[0]["display_content"])


@override_settings(JWT_SECRET_KEY=TEST_JWT_SECRET)
class HealthViewTest(TestCase):
    """Tests for the health check endpoint."""

    def test_health_endpoint_is_public(self):
        """Health endpoint is accessible without authentication."""
        response = self.client.get("/api/chat/health/")
        # May be 200 (all healthy) or 503 (degraded) — but never 401
        self.assertNotEqual(response.status_code, 401)
        self.assertIn("status", response.json())
        self.assertIn("checks", response.json())
