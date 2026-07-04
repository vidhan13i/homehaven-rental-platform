from rest_framework import serializers
from notification.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "payload",
            "is_read",
            "is_archived",
            "priority",
            "created_at",
            "read_at",
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        exclude = ["user_id", "created_at", "updated_at"]
