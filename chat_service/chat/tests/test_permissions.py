"""
Unit tests for permission logic.
"""

import uuid
from django.test import TestCase

from chat.models import Conversation
from chat.services.permission_service import PermissionService


def _make_conversation(owner_id=None, renter_id=None, listing_id=None) -> Conversation:
    """Create an unsaved Conversation for testing."""
    conv = Conversation()
    conv.id = uuid.uuid4()
    conv.owner_id = uuid.UUID(str(owner_id or uuid.uuid4()))
    conv.renter_id = uuid.UUID(str(renter_id or uuid.uuid4()))
    conv.listing_id = uuid.UUID(str(listing_id or uuid.uuid4()))
    conv.is_blocked = False
    return conv


class ConversationPermissionTest(TestCase):
    """Tests for PermissionService."""

    def setUp(self):
        self.owner_id = str(uuid.uuid4())
        self.renter_id = str(uuid.uuid4())
        self.third_party_id = str(uuid.uuid4())
        self.conversation = _make_conversation(
            owner_id=self.owner_id,
            renter_id=self.renter_id,
        )

    def test_owner_can_access(self):
        result = PermissionService.can_access_conversation(
            self.owner_id, self.conversation
        )
        self.assertTrue(result)

    def test_renter_can_access(self):
        result = PermissionService.can_access_conversation(
            self.renter_id, self.conversation
        )
        self.assertTrue(result)

    def test_third_party_cannot_access(self):
        result = PermissionService.can_access_conversation(
            self.third_party_id, self.conversation
        )
        self.assertFalse(result)

    def test_owner_can_send_message(self):
        allowed, reason = PermissionService.can_send_message(
            self.owner_id, self.conversation
        )
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_third_party_cannot_send_message(self):
        allowed, reason = PermissionService.can_send_message(
            self.third_party_id, self.conversation
        )
        self.assertFalse(allowed)
        self.assertIn("participant", reason)

    def test_blocked_conversation_cannot_send_message(self):
        self.conversation.is_blocked = True
        allowed, reason = PermissionService.can_send_message(
            self.owner_id, self.conversation
        )
        self.assertFalse(allowed)
        self.assertIn("blocked", reason)

    def test_is_participant_owner(self):
        self.assertTrue(self.conversation.is_participant(self.owner_id))

    def test_is_participant_renter(self):
        self.assertTrue(self.conversation.is_participant(self.renter_id))

    def test_is_not_participant_third_party(self):
        self.assertFalse(self.conversation.is_participant(self.third_party_id))

    def test_get_other_participant_from_owner(self):
        other = self.conversation.get_other_participant(self.owner_id)
        self.assertEqual(other, self.renter_id)

    def test_get_other_participant_from_renter(self):
        other = self.conversation.get_other_participant(self.renter_id)
        self.assertEqual(other, self.owner_id)

    def test_get_other_participant_third_party_returns_none(self):
        other = self.conversation.get_other_participant(self.third_party_id)
        self.assertIsNone(other)

    def test_can_modify_message_sender(self):
        sender_id = str(uuid.uuid4())
        self.assertTrue(PermissionService.can_modify_message(sender_id, sender_id))

    def test_cannot_modify_other_users_message(self):
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        self.assertFalse(PermissionService.can_modify_message(user_a, user_b))
