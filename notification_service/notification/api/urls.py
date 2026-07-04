from django.urls import path, include
from rest_framework.routers import DefaultRouter

from notification.api.views import (
    NotificationViewSet,
    NotificationPreferenceView,
    HealthView,
)

router = DefaultRouter()
router.register(r"list", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    path("preferences/", NotificationPreferenceView.as_view(), name="preferences"),
    path("health/", HealthView.as_view(), name="health"),
]
