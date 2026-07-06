"""
REST API Views for chat_service.

ConversationViewSet  — Full CRUD + lifecycle actions for conversations
MessageViewSet       — CRUD + react/star/forward/search for messages
PresenceView         — Read-only presence endpoint
HealthView           — Health + readiness check

Design:
  - Views call Services; Services call Repositories.
  - Views never directly call Repository methods.
  - Views never directly import ORM models for queries.
  - IsAuthenticated is the base permission; IsConversationParticipant
    enforces object-level access control.
"""

import logging
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from shared_lib.kafka.producer import KafkaEventProducer
from shared_lib.kafka.events import build_event
from shared_lib.kafka.topics import Topics

_kafka_producer = KafkaEventProducer()

from django.db.models import Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from chat.models import Conversation, Message
from chat.services import (
    ConversationService,
    MessageService,
    PresenceService,
)
from chat.repositories import MessageRepository, ConversationRepository
from chat.permissions import IsConversationParticipant, IsMessageSender
from chat.api.serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageListSerializer,
    MessageCreateSerializer,
    MessageEditSerializer,
    ReactionSerializer,
)
from chat.api.filters import ConversationFilter, MessageFilter
from chat.api.pagination import ChatPagination, MessagePagination

logger = logging.getLogger("chat.api.views")


from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample


@extend_schema_view(
    list=extend_schema(summary="List Conversations", tags=["Chat"]),
    retrieve=extend_schema(summary="Retrieve Conversation", tags=["Chat"]),
    create=extend_schema(
        summary="Create Conversation",
        tags=["Chat"],
        examples=[
            OpenApiExample(
                "Create Chat", value={"participant_id": "123"}, request_only=True
            )
        ],
    ),
    update=extend_schema(summary="Update Conversation", tags=["Chat"]),
    partial_update=extend_schema(
        summary="Partially Update Conversation", tags=["Chat"]
    ),
    destroy=extend_schema(summary="Delete Conversation", tags=["Chat"]),
)
class ConversationViewSet(viewsets.ModelViewSet):
    """
    REST API for Conversations.

    GET    /api/chat/conversations/                → list
    POST   /api/chat/conversations/                → create
    GET    /api/chat/conversations/<id>/           → detail
    DELETE /api/chat/conversations/<id>/           → delete
    POST   /api/chat/conversations/<id>/archive/   → toggle archive
    POST   /api/chat/conversations/<id>/pin/        → toggle pin
    POST   /api/chat/conversations/<id>/block/      → block
    POST   /api/chat/conversations/<id>/unblock/    → unblock
    POST   /api/chat/conversations/<id>/mark_read/  → mark all messages read
    GET    /api/chat/conversations/<id>/unread_count/→ get unread count
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ConversationFilter
    ordering_fields = ["last_message_at", "created_at"]
    ordering = ["-is_pinned", "-last_message_at"]
    pagination_class = ChatPagination

    def get_queryset(self):
        """Only return conversations the authenticated user participates in."""
        user_id = str(self.request.user.id)
        return Conversation.objects.filter(
            Q(owner_id=user_id) | Q(renter_id=user_id)
        ).order_by("-is_pinned", "-last_message_at", "-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return ConversationListSerializer
        if self.action == "create":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_object(self):
        """Override to enforce participant permission on object-level access."""
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self):
        if self.action in [
            "retrieve",
            "destroy",
            "archive",
            "pin",
            "block",
            "unblock",
            "mark_read",
            "unread_count",
        ]:
            return [IsAuthenticated(), IsConversationParticipant()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """
        POST /api/chat/conversations/
        Creates or returns an existing conversation.
        """
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            conversation, created = ConversationService.create_conversation(
                listing_id=str(data["listing_id"]),
                owner_id=str(data["owner_id"]),
                renter_id=str(data["renter_id"]),
                requesting_user_id=str(request.user.id),
            )
        except (ValueError, PermissionError) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = ConversationSerializer(conversation)
        return Response(
            out_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/chat/conversations/<id>/"""
        conversation = self.get_object()
        deleted = ConversationService.delete_conversation(
            str(conversation.id), str(request.user.id)
        )
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"error": "Could not delete conversation"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """POST /api/chat/conversations/<id>/archive/ — toggle archive"""
        conversation = self.get_object()
        new_state = not conversation.is_archived
        ConversationService.archive_conversation(
            str(conversation.id), str(request.user.id), archived=new_state
        )
        return Response({"archived": new_state})

    @action(detail=True, methods=["post"])
    def pin(self, request, pk=None):
        """POST /api/chat/conversations/<id>/pin/ — toggle pin"""
        conversation = self.get_object()
        new_state = not conversation.is_pinned
        ConversationService.pin_conversation(
            str(conversation.id), str(request.user.id), pinned=new_state
        )
        return Response({"pinned": new_state})

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        """POST /api/chat/conversations/<id>/block/"""
        conversation = self.get_object()
        ConversationService.block_conversation(
            str(conversation.id), str(request.user.id), blocked=True
        )
        return Response({"blocked": True})

    @action(detail=True, methods=["post"])
    def unblock(self, request, pk=None):
        """POST /api/chat/conversations/<id>/unblock/"""
        conversation = self.get_object()
        ConversationService.block_conversation(
            str(conversation.id), str(request.user.id), blocked=False
        )
        return Response({"blocked": False})

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        """POST /api/chat/conversations/<id>/mark_read/ — mark all messages read"""
        conversation = self.get_object()
        count = MessageService.mark_seen(
            conversation_id=str(conversation.id),
            user_id=str(request.user.id),
        )
        return Response({"marked_as_read": count})

    @action(detail=True, methods=["get"], url_path="unread_count")
    def unread_count(self, request, pk=None):
        """GET /api/chat/conversations/<id>/unread_count/"""
        conversation = self.get_object()
        count = MessageService.get_unread_count(
            conversation_id=str(conversation.id),
            user_id=str(request.user.id),
        )
        return Response({"unread_count": count})


@extend_schema_view(
    list=extend_schema(summary="List Messages", tags=["Chat"]),
    retrieve=extend_schema(summary="Retrieve Message", tags=["Chat"]),
    create=extend_schema(
        summary="Create Message",
        tags=["Chat"],
        examples=[
            OpenApiExample(
                "Send Message", value={"content": "Hello"}, request_only=True
            )
        ],
    ),
    update=extend_schema(summary="Update Message", tags=["Chat"]),
    partial_update=extend_schema(summary="Partially Update Message", tags=["Chat"]),
    destroy=extend_schema(summary="Delete Message", tags=["Chat"]),
)
class MessageViewSet(viewsets.ModelViewSet):
    """
    REST API for Messages.

    GET    /api/chat/messages/?conversation=<id>  → list messages
    POST   /api/chat/messages/                     → send message
    GET    /api/chat/messages/<id>/                → detail
    PATCH  /api/chat/messages/<id>/                → edit
    DELETE /api/chat/messages/<id>/                → soft delete
    POST   /api/chat/messages/<id>/react/           → add/remove reaction
    POST   /api/chat/messages/<id>/forward/         → forward message
    POST   /api/chat/messages/<id>/star/            → star/unstar
    GET    /api/chat/messages/search/?q=<q>&conversation=<id> → search
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MessageFilter
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    pagination_class = MessagePagination
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user_id = str(self.request.user.id)

        if self.action == "list":
            conversation_id = self.request.query_params.get("conversation")
            if not conversation_id:
                return Message.objects.none()
            user_conversations = Conversation.objects.filter(
                Q(owner_id=user_id) | Q(renter_id=user_id),
                id=conversation_id,
            )
            if not user_conversations.exists():
                return Message.objects.none()
            return (
                Message.objects.filter(
                    conversation_id=conversation_id, deleted_at__isnull=True
                )
                .select_related("reply_to")
                .order_by("-created_at")
            )

        # detail-style actions (retrieve/update/partial_update/destroy/react/forward/star):
        # authorize via the message's own conversation, not a query param.
        return Message.objects.filter(
            Q(conversation__owner_id=user_id) | Q(conversation__renter_id=user_id),
            deleted_at__isnull=True,
        ).select_related("reply_to")

    def get_serializer_class(self):
        if self.action == "list":
            return MessageListSerializer
        if self.action == "create":
            return MessageCreateSerializer
        if self.action == "partial_update":
            return MessageEditSerializer
        return MessageSerializer

    def get_permissions(self):
        if self.action in ["partial_update", "destroy"]:
            return [IsAuthenticated(), IsMessageSender()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """POST /api/chat/messages/ — send a message via REST API"""
        conversation_id = request.data.get("conversation")
        if not conversation_id:
            return Response(
                {"error": "conversation is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = ConversationRepository.get_by_id(conversation_id)
        if not conversation:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not conversation.is_participant(str(request.user.id)):
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        message, error = MessageService.send_message(
            conversation=conversation,
            sender_id=str(request.user.id),
            content=data.get("content", ""),
            message_type=data.get("message_type", "text"),
            attachment=data.get("attachment"),
            attachment_name=data.get("attachment_name"),
            attachment_size=data.get("attachment_size"),
            reply_to_id=str(data["reply_to"].id) if data.get("reply_to") else None,
        )

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        message_data = MessageSerializer(message).data
        # msgpack cannot serialize UUID objects; convert all to primitive strings first
        safe_message_data = json.loads(json.dumps(message_data, default=str))

        # Broadcast via Channel Layer so connected WebSockets receive it in real-time
        channel_layer = get_channel_layer()
        group_name = f"chat_{conversation.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "broadcast.receive_message",
                "message": safe_message_data,
            },
        )

        # Publish MessageSent domain event to Kafka (fire-and-forget)
        # notification_service consumes this to push in-app and email notifications
        try:
            # Determine the recipient (the other participant in the conversation)
            participants = [conversation.owner_id, conversation.renter_id]
            sender_id = str(request.user.id)
            recipient_id = next((p for p in participants if str(p) != sender_id), None)
            kafka_event = build_event(
                event_type="MessageSent",
                aggregate_id=str(message.id),
                source_service="chat_service",
                payload={
                    "message_id": str(message.id),
                    "conversation_id": str(conversation.id),
                    "sender_id": sender_id,
                    "recipient_id": str(recipient_id) if recipient_id else None,
                    "content_preview": (message.content or "")[:100],
                    "message_type": message.message_type,
                },
            )
            _kafka_producer.publish_async(
                Topics.CHAT_MESSAGE_SENT, kafka_event, key=str(conversation.id)
            )
        except Exception as exc:
            logger.error("Failed to publish MessageSent event: %s", exc)

        return Response(
            message_data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/chat/messages/<id>/ — edit message content"""
        message = self.get_object()
        serializer = MessageEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated, error = MessageService.edit_message(
            message_id=str(message.id),
            user_id=str(request.user.id),
            new_content=serializer.validated_data["content"],
        )

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MessageSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/chat/messages/<id>/ — soft delete"""
        message = self.get_object()
        success, error = MessageService.delete_message(
            message_id=str(message.id),
            user_id=str(request.user.id),
        )
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def react(self, request, pk=None):
        """POST /api/chat/messages/<id>/react/ — toggle reaction"""
        serializer = ReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message, error = MessageService.add_reaction(
            message_id=pk,
            user_id=str(request.user.id),
            emoji=serializer.validated_data["emoji"],
        )

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MessageSerializer(message).data)

    @action(detail=True, methods=["post"])
    def star(self, request, pk=None):
        """POST /api/chat/messages/<id>/star/ — star/unstar"""
        message, error = MessageService.toggle_star(
            message_id=pk,
            user_id=str(request.user.id),
        )

        if error:
            return Response({"error": error}, status=status.HTTP_404_NOT_FOUND)

        is_starred = str(request.user.id) in (message.starred_by or [])
        return Response(
            {"starred": is_starred, "message": MessageSerializer(message).data}
        )

    @action(detail=True, methods=["post"])
    def forward(self, request, pk=None):
        """POST /api/chat/messages/<id>/forward/ — forward to another conversation"""
        target_conversation_id = request.data.get("conversation_id")
        if not target_conversation_id:
            return Response(
                {"error": "conversation_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate original message
        original = MessageRepository.get_by_id(pk)
        if not original or original.is_deleted:
            return Response(
                {"error": "Message not found or deleted"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate target conversation
        target_conversation = ConversationRepository.get_by_id(target_conversation_id)
        if not target_conversation or not target_conversation.is_participant(
            str(request.user.id)
        ):
            return Response(
                {"error": "Target conversation not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )

        forwarded, error = MessageService.send_message(
            conversation=target_conversation,
            sender_id=str(request.user.id),
            content=original.content,
            message_type=original.message_type,
            attachment=original.attachment,
        )

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            MessageSerializer(forwarded).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def search(self, request):
        """GET /api/chat/messages/search/?q=<query>&conversation=<id>"""
        query = request.query_params.get("q", "").strip()
        conversation_id = request.query_params.get("conversation")

        if not query:
            return Response(
                {"error": "q parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not conversation_id:
            return Response(
                {"error": "conversation parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages = MessageService.search_messages(
            conversation_id=conversation_id,
            query=query,
            user_id=str(request.user.id),
        )

        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)


class PresenceView(APIView):
    """
    GET /api/chat/presence/<user_id>/
    Returns the online status and last seen time of any user.
    Only accessible by authenticated users.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id: str):
        presence_data = PresenceService.get_presence(user_id)
        return Response(presence_data)


class HealthView(APIView):
    """
    GET /api/chat/health/
    Service health check for Docker healthcheck and load balancer probes.
    Returns DB connectivity, Redis Channel Layer connectivity.
    """

    permission_classes = []  # Public — no auth required for health checks

    def get(self, request):
        health = {
            "status": "ok",
            "service": "chat_service",
            "checks": {},
        }
        overall_ok = True

        try:
            from django.db import connections

            connections["chat"].ensure_connection()
            health["checks"]["database"] = "ok"
        except Exception as exc:
            health["checks"]["database"] = f"error: {str(exc)}"
            overall_ok = False

        try:
            import redis
            from django.conf import settings

            r = redis.from_url(
                settings.CHANNEL_LAYERS_REDIS_URL, socket_connect_timeout=2
            )
            r.ping()
            health["checks"]["channel_layer"] = "ok"
        except Exception as exc:
            health["checks"]["channel_layer"] = f"error: {str(exc)}"
            overall_ok = False

        try:
            import redis
            from django.conf import settings

            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            r.ping()
            health["checks"]["redis_cache"] = "ok"
        except Exception as exc:
            health["checks"]["redis_cache"] = f"error: {str(exc)}"
            overall_ok = False

        if not overall_ok:
            health["status"] = "degraded"

        return Response(
            health,
            status=(
                status.HTTP_200_OK
                if overall_ok
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )
