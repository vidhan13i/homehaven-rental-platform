"""Root URL configuration for chat_service."""

from django.contrib import admin
from django.urls import path, include


from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # OpenAPI Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Django admin (scoped to /admin/chat/ to match Nginx routing convention)
    path("admin/chat/", admin.site.urls),
    # All REST API endpoints for the chat service
    path("api/chat/", include("chat.urls")),
]
