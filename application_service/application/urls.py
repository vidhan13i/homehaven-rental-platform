from django.urls import path, include
from rest_framework.routers import DefaultRouter
from application.api.views import ApplicationViewSet, ApplicantViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r"applications", ApplicationViewSet, basename="application")
router.register(r"applicants", ApplicantViewSet, basename="applicant")
router.register(r"documents", DocumentViewSet, basename="document")

app_name = "application_api"

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
