from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from notification.models import Notification
from notification.services.notification_service import NotificationService
from notification.repositories.notification_repository import PreferenceRepository
from notification.api.serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only CRUD for notifications (created only by Kafka consumers).
    Plus custom actions for mark-read, archive, and delete.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = str(self.request.user.id)
        # We rely on NotificationService for the query, but DRF pagination needs a queryset
        qs, _ = NotificationService.get_for_user(
            user_id=user_id,
            is_archived=False,
            limit=1000, # Handled by pagination class
        )
        return qs

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get total unread notifications count."""
        count = NotificationService.get_unread_count(str(request.user.id))
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = NotificationService.mark_as_read(pk, str(request.user.id))
        if not notification:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all unread notifications as read."""
        updated = NotificationService.mark_all_as_read(str(request.user.id))
        return Response({"updated_count": updated})

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive a notification (soft delete)."""
        notification = NotificationService.archive(pk, str(request.user.id))
        if not notification:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        """Hard delete a notification."""
        success = NotificationService.delete(kwargs.get("pk"), str(request.user.id))
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)


class NotificationPreferenceView(APIView):
    """
    GET/PATCH user notification preferences.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = PreferenceRepository.get_or_create_for_user(str(request.user.id))
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)

    def patch(self, request):
        prefs = PreferenceRepository.update(str(request.user.id), **request.data)
        if not prefs:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(NotificationPreferenceSerializer(prefs).data)


class HealthView(APIView):
    """Health check endpoint for Docker/Nginx."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({"status": "ok", "service": "notification_service"})
