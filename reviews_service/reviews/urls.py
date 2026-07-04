from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reviews.api.views import ReviewViewSet

router = DefaultRouter()
router.register(r"reviews", ReviewViewSet, basename="review")

app_name = "reviews_api"

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
