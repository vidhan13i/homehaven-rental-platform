"""
WebSocket consumer tests using channels.testing.WebsocketCommunicator.

These tests verify the full WebSocket lifecycle:
  - Authentication (valid JWT, expired JWT, missing JWT)
  - Authorization (participant, non-participant)
  - Event routing (send_message, typing, heartbeat, mark_read)
  - Broadcast events
"""
import uuid
import time
import jwt

from django.test import TestCase, override_settings
from channels.testing import WebsocketCommunicator

from chat.models import Conversation
from config.asgi import application

TEST_JWT_SECRET = "test-consumer-secret"


def _make_jwt(user_id: str, username: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "email": f"{username}@test.com",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def _make_expired_jwt(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "username": "user",
        "exp": int(time.time()) - 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def _create_conversation(owner_id: str, renter_id: str) -> Conversation:
    return Conversation.objects.using("chat").create(
        listing_id=uuid.uuid4(),
        owner_id=uuid.UUID(owner_id),
        renter_id=uuid.UUID(renter_id),
    )


@override_settings(
    JWT_SECRET_KEY=TEST_JWT_SECRET,
    CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    },
)
class ChatConsumerTest(TestCase):
    """WebSocket consumer integration tests using in-memory channel layer."""

    databases = {"default", "chat"}

    def setUp(self):
        self.owner_id = str(uuid.uuid4())
        self.renter_id = str(uuid.uuid4())
        self.owner_token = _make_jwt(self.owner_id, "owner")
        self.renter_token = _make_jwt(self.renter_id, "renter")
        self.conversation = _create_conversation(self.owner_id, self.renter_id)
        self.ws_url = f"/ws/chat/{self.conversation.id}/?token={self.owner_token}"

    async def _connect(self, token: str = None, conversation_id: str = None) -> WebsocketCommunicator:
        """Helper to create and connect a WebSocket communicator."""
        conv_id = conversation_id or str(self.conversation.id)
        tok = token or self.owner_token
        url = f"/ws/chat/{conv_id}/?token={tok}"
        communicator = WebsocketCommunicator(application, url)
        return communicator

    async def test_valid_jwt_connects_successfully(self):
        communicator = await self._connect()
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Should receive 'connected' message
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "connected")
        self.assertEqual(response["conversation_id"], str(self.conversation.id))

        await communicator.disconnect()

    async def test_invalid_jwt_is_rejected(self):
        communicator = await self._connect(token="not.a.valid.jwt")
        connected, code = await communicator.connect()
        # Should be rejected with close code 4001
        self.assertFalse(connected)

    async def test_expired_jwt_is_rejected(self):
        expired_token = _make_expired_jwt(self.owner_id)
        communicator = await self._connect(token=expired_token)
        connected, code = await communicator.connect()
        self.assertFalse(connected)

    async def test_non_participant_is_rejected(self):
        stranger_id = str(uuid.uuid4())
        stranger_token = _make_jwt(stranger_id, "stranger")
        communicator = await self._connect(token=stranger_token)
        connected, code = await communicator.connect()
        self.assertFalse(connected)

    async def test_nonexistent_conversation_is_rejected(self):
        fake_id = str(uuid.uuid4())
        communicator = await self._connect(conversation_id=fake_id)
        connected, code = await communicator.connect()
        self.assertFalse(connected)

    async def test_send_message_event(self):
        communicator = await self._connect()
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Consume the 'connected' and 'user_online' messages
        await communicator.receive_json_from()  # connected
        # (user_online may or may not be received depending on timing)

        # Send a message
        await communicator.send_json_to({
            "type": "send_message",
            "content": "Hello from test!",
            "message_type": "text",
        })

        # Should receive receive_message broadcast
        response = None
        for _ in range(5):  # Try a few times in case of other events
            msg = await communicator.receive_json_from()
            if msg.get("type") == "receive_message":
                response = msg
                break

        self.assertIsNotNone(response)
        self.assertEqual(response["type"], "receive_message")
        self.assertEqual(response["message"]["content"], "Hello from test!")
        self.assertEqual(response["message"]["sender_id"], self.owner_id)

        await communicator.disconnect()

    async def test_typing_event(self):
        """Owner sends typing → renter receives user_typing."""
        owner_comm = await self._connect(token=self.owner_token)
        renter_comm = await self._connect(token=self.renter_token)

        await owner_comm.connect()
        await renter_comm.connect()

        # Consume connection events
        await owner_comm.receive_json_from()
        await renter_comm.receive_json_from()

        # Owner sends typing
        await owner_comm.send_json_to({"type": "typing"})

        # Renter should receive user_typing
        response = None
        for _ in range(5):
            msg = await renter_comm.receive_json_from()
            if msg.get("type") == "user_typing":
                response = msg
                break

        self.assertIsNotNone(response)
        self.assertEqual(response["user_id"], self.owner_id)

        await owner_comm.disconnect()
        await renter_comm.disconnect()

    async def test_heartbeat_responds_with_pong(self):
        communicator = await self._connect()
        await communicator.connect()
        await communicator.receive_json_from()  # connected

        await communicator.send_json_to({"type": "heartbeat"})

        # Should receive pong
        response = None
        for _ in range(5):
            msg = await communicator.receive_json_from()
            if msg.get("type") == "pong":
                response = msg
                break

        self.assertIsNotNone(response)
        self.assertEqual(response["type"], "pong")

        await communicator.disconnect()

    async def test_unknown_event_returns_error(self):
        communicator = await self._connect()
        await communicator.connect()
        await communicator.receive_json_from()  # connected

        await communicator.send_json_to({"type": "nonexistent_event"})

        response = None
        for _ in range(5):
            msg = await communicator.receive_json_from()
            if msg.get("type") == "error":
                response = msg
                break

        self.assertIsNotNone(response)
        self.assertEqual(response["type"], "error")

        await communicator.disconnect()

    async def test_invalid_json_returns_error(self):
        communicator = await self._connect()
        await communicator.connect()
        await communicator.receive_json_from()  # connected

        await communicator.send_to(text_data="not valid json at all {{{")

        response = None
        for _ in range(5):
            msg = await communicator.receive_json_from()
            if msg.get("type") == "error":
                response = msg
                break

        self.assertIsNotNone(response)

        await communicator.disconnect()
