from django.urls import path, include
from rest_framework.routers import DefaultRouter
from profiles_app.api.views import ProfileViewSet, EmailOTPViewSet

router = DefaultRouter()
router.register(r"profiles", ProfileViewSet, basename="profile")
router.register(r"otp", EmailOTPViewSet, basename="otp")

app_name = "profiles_api"

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
