"""
ChatConsumer — AsyncWebsocketConsumer for real-time messaging.

Design principle: THIN CONSUMER
  - Consumer handles WebSocket protocol (connect, disconnect, receive, send)
  - Consumer does NOT contain business logic
  - All business logic lives in the service layer

WebSocket event types (client → server):
  send_message       Send a new message
  typing             User started typing
  stop_typing        User stopped typing
  message_seen       Mark specific message as seen
  mark_read          Mark all messages in conversation as read
  heartbeat          Keep presence alive (every 30s)

WebSocket event types (server → client):
  connected          Connection accepted + conversation state
  receive_message    New message broadcast
  message_edited     Edited message broadcast
  message_deleted    Soft-deleted message broadcast
  message_delivered  Delivery receipt
  message_seen       Read receipt
  user_typing        Typing indicator
  user_stop_typing   Typing indicator cleared
  user_online        User came online
  user_offline       User went offline
  error              Error response
  pong               Heartbeat response

Close codes:
  4001  Unauthorized (invalid/expired JWT)
  4003  Forbidden (not a participant in this conversation)
  4004  Conversation not found
  4005  Conversation is blocked
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from chat.authentication.websocket import (
    authenticate_websocket_token,
    extract_token_from_scope,
    WS_CLOSE_CODE_UNAUTHORIZED,
    WS_CLOSE_CODE_FORBIDDEN,
)
from chat.services.permission_service import PermissionService
from chat.services.message_service import MessageService
from chat.services.presence_service import PresenceService
from chat.services.notification_service import NotificationService

logger = logging.getLogger("chat.consumer")


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Production WebSocket consumer for real-time chat.

    One consumer instance per WebSocket connection.
    Each connection is associated with exactly one conversation group.

    Lifecycle:
      websocket_connect  →  authenticate → authorize → join group → accept
      receive            →  route to handler by event type
      websocket_disconnect → leave group → set offline → broadcast
    """

    # Connection lifecycle

    async def websocket_connect(self, message: dict) -> None:
        """
        Called when a WebSocket connection is initiated.
        Handles authentication and authorization BEFORE accepting the connection.
        """
        self.conversation_id: str = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name: str = f"chat_{self.conversation_id}"
        self.user = None
        self.conversation = None

        token = extract_token_from_scope(self.scope)
        user = authenticate_websocket_token(token)

        if user is None:
            logger.warning(
                "WebSocket rejected: invalid/missing JWT for conversation %s",
                self.conversation_id,
            )
            await self.close(code=WS_CLOSE_CODE_UNAUTHORIZED)
            return

        self.user = user

        allowed, conversation = await PermissionService.async_can_access_conversation(
            user_id=str(self.user.id),
            conversation_id=self.conversation_id,
        )

        if not allowed or conversation is None:
            logger.warning(
                "WebSocket rejected: user %s not authorized for conversation %s",
                self.user.id,
                self.conversation_id,
            )
            await self.close(code=WS_CLOSE_CODE_FORBIDDEN)
            return

        self.conversation = conversation

        if conversation.is_blocked:
            logger.info(
                "WebSocket for blocked conversation %s accepted (read-only mode)",
                self.conversation_id,
            )
            # Still allow connection but message sending will be rejected by service

        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

        await PresenceService.async_set_online(str(self.user.id))

        logger.info(
            "WebSocket connected: user=%s, conversation=%s, channel=%s",
            self.user.id,
            self.conversation_id,
            self.channel_name,
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast.user_online",
                "user_id": str(self.user.id),
                "username": self.user.username,
            },
        )

        other_user_id = (
            str(self.conversation.renter_id)
            if str(self.user.id) == str(self.conversation.owner_id)
            else str(self.conversation.owner_id)
        )
        from asgiref.sync import sync_to_async

        other_user_online = await sync_to_async(PresenceService.is_online)(
            other_user_id
        )

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connected",
                    "conversation_id": self.conversation_id,
                    "user_id": str(self.user.id),
                    "other_user_id": other_user_id,
                    "other_user_online": other_user_online,
                }
            )
        )

    async def websocket_disconnect(self, close_code: int) -> None:
        """
        Called when the WebSocket connection closes (client or server side).
        Always clean up group membership and presence, even on unexpected close.
        """
        if self.user:
            await PresenceService.async_set_offline(str(self.user.id))

            # Broadcast offline status to conversation group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "broadcast.user_offline",
                    "user_id": str(self.user.id),
                    "username": getattr(self.user, "username", None),
                },
            )

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        logger.info(
            "WebSocket disconnected: user=%s, conversation=%s, code=%s",
            getattr(self, "user", {}) and self.user.id,
            getattr(self, "conversation_id", "unknown"),
            close_code,
        )

    # Receive: client → server

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        """
        Route incoming WebSocket messages to the appropriate handler.
        All business logic is in service methods — consumer only routes.
        """
        if not self.user:
            # Connection wasn't properly authenticated — reject all messages
            await self._send_error("Not authenticated")
            return

        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
            return

        event_type = data.get("type")
        handlers = {
            "send_message": self._handle_send_message,
            "typing": self._handle_typing,
            "stop_typing": self._handle_stop_typing,
            "message_seen": self._handle_message_seen,
            "mark_read": self._handle_mark_read,
            "heartbeat": self._handle_heartbeat,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(data)
        else:
            await self._send_error(f"Unknown event type: {event_type!r}")

    # Handlers: process client events

    async def _handle_send_message(self, data: dict) -> None:
        """Handle a send_message event from the client."""
        content = data.get("content", "")
        message_type = data.get("message_type", "text")
        reply_to_id = data.get("reply_to_id")

        message, error = await MessageService.async_send_message(
            conversation=self.conversation,
            sender_id=str(self.user.id),
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
        )

        if error:
            await self._send_error(error)
            return

        # Serialize the message for broadcast
        message_data = self._serialize_message(message)

        # Broadcast to ALL clients in the conversation group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast.receive_message",
                "message": message_data,
            },
        )

        # Queue offline notification for the recipient if they're offline
        await NotificationService.async_notify_if_offline(
            message=message,
            conversation=self.conversation,
        )

    async def _handle_typing(self, data: dict) -> None:
        """Broadcast typing indicator to all other participants."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast.user_typing",
                "user_id": str(self.user.id),
                "username": self.user.username,
            },
        )

    async def _handle_stop_typing(self, data: dict) -> None:
        """Broadcast stop-typing indicator."""
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast.user_stop_typing",
                "user_id": str(self.user.id),
                "username": self.user.username,
            },
        )

    async def _handle_message_seen(self, data: dict) -> None:
        """Mark a specific message as seen and broadcast read receipt."""
        message_id = data.get("message_id")
        if not message_id:
            await self._send_error("message_id is required")
            return

        from asgiref.sync import sync_to_async
        from chat.repositories import MessageRepository

        await sync_to_async(MessageRepository.mark_seen)(message_id)

        # Broadcast read receipt to the conversation group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast.message_seen",
                "message_id": message_id,
                "user_id": str(self.user.id),
            },
        )

    async def _handle_mark_read(self, data: dict) -> None:
        """Mark ALL messages in this conversation as read."""
        count = await MessageService.async_mark_seen(
            conversation_id=self.conversation_id,
            user_id=str(self.user.id),
        )
        await self.send(
            text_data=json.dumps(
                {
                    "type": "mark_read_ack",
                    "conversation_id": self.conversation_id,
                    "marked_count": count,
                }
            )
        )

    async def _handle_heartbeat(self, data: dict) -> None:
        """Refresh presence TTL on heartbeat. Respond with pong."""
        await PresenceService.async_refresh(str(self.user.id))
        await self.send(
            text_data=json.dumps(
                {
                    "type": "pong",
                    "user_id": str(self.user.id),
                }
            )
        )

    # Broadcast handlers: channel layer → WebSocket
    # These are called by the Channel Layer when group_send fires.
    # Method names MUST match the "type" field in group_send (dots → underscores).

    async def broadcast_receive_message(self, event: dict) -> None:
        """Forward a new message to this WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "receive_message",
                    "message": event["message"],
                }
            )
        )

    async def broadcast_user_typing(self, event: dict) -> None:
        """Forward typing indicator (only to other clients, not the sender)."""
        if event.get("user_id") != str(self.user.id):
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_typing",
                        "user_id": event["user_id"],
                        "username": event.get("username"),
                    }
                )
            )

    async def broadcast_user_stop_typing(self, event: dict) -> None:
        """Forward stop-typing indicator."""
        if event.get("user_id") != str(self.user.id):
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "user_stop_typing",
                        "user_id": event["user_id"],
                        "username": event.get("username"),
                    }
                )
            )

    async def broadcast_message_seen(self, event: dict) -> None:
        """Forward read receipt."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_seen",
                    "message_id": event["message_id"],
                    "user_id": event["user_id"],
                }
            )
        )

    async def broadcast_user_online(self, event: dict) -> None:
        """Forward user_online presence event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_online",
                    "user_id": event["user_id"],
                    "username": event.get("username"),
                }
            )
        )

    async def broadcast_user_offline(self, event: dict) -> None:
        """Forward user_offline presence event."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_offline",
                    "user_id": event["user_id"],
                    "username": event.get("username"),
                }
            )
        )

    async def broadcast_message_edited(self, event: dict) -> None:
        """Forward edited message to this client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_edited",
                    "message": event["message"],
                }
            )
        )

    async def broadcast_message_deleted(self, event: dict) -> None:
        """Forward soft-delete notification."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message_deleted",
                    "message_id": event["message_id"],
                }
            )
        )

    # Helpers

    async def _send_error(self, detail: str) -> None:
        """Send an error message to this client only."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "detail": detail,
                }
            )
        )

    @staticmethod
    def _serialize_message(message) -> dict:
        """Convert a Message model instance to a JSON-serializable dict."""
        return {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "sender_id": str(message.sender_id),
            "content": message.display_content,
            "message_type": message.message_type,
            "attachment": message.attachment,
            "attachment_name": message.attachment_name,
            "reply_to_id": str(message.reply_to_id) if message.reply_to_id else None,
            "forwarded_from": (
                str(message.forwarded_from) if message.forwarded_from else None
            ),
            "is_edited": message.is_edited,
            "is_deleted": message.is_deleted,
            "reactions": message.reactions,
            "starred_by": message.starred_by,
            "delivered_at": (
                message.delivered_at.isoformat() if message.delivered_at else None
            ),
            "seen_at": message.seen_at.isoformat() if message.seen_at else None,
            "created_at": message.created_at.isoformat(),
        }
