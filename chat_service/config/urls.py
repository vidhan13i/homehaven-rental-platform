"""Root URL configuration for chat_service."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin (scoped to /admin/chat/ to match Nginx routing convention)
    path("admin/chat/", admin.site.urls),
    # All REST API endpoints for the chat service
    path("api/chat/", include("chat.urls")),
]
