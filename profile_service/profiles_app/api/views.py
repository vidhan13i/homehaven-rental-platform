import random
import string
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.core.cache import cache
import requests
from shared_lib.resilience import make_resilient_request

from profiles_app.models import Profile
from profiles_app.api.serializers import (
    ProfileSerializer,
    ProfileListSerializer,
    ProfileCreateUpdateSerializer,
    EmailOTPRequestSerializer,
    EmailOTPVerifySerializer,
)
from profiles_app.tasks import send_otp_email, send_profile_creation_event
from profiles_app.throttles import OTPRequestThrottle, OTPVerifyThrottle
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
)


@extend_schema_view(
    list=extend_schema(summary="List all Profiles", tags=["Profiles"]),
    retrieve=extend_schema(summary="Retrieve a Profile", tags=["Profiles"]),
    create=extend_schema(
        summary="Create a Profile",
        tags=["Profiles"],
        responses={201: ProfileSerializer},
    ),
    update=extend_schema(summary="Update a Profile", tags=["Profiles"]),
    partial_update=extend_schema(
        summary="Partially Update a Profile", tags=["Profiles"]
    ),
    destroy=extend_schema(summary="Delete a Profile", tags=["Profiles"]),
    by_email=extend_schema(
        summary="Lookup by Email",
        tags=["Profiles"],
        parameters=[
            OpenApiParameter(
                name="email",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Email of the user",
            )
        ],
        responses={
            200: ProfileSerializer,
            400: OpenApiResponse(description="Email parameter missing"),
            404: OpenApiResponse(description="Profile not found"),
        },
    ),
    reviews=extend_schema(
        summary="Get Reviews by Profile",
        tags=["Profiles (External)"],
        description="Fetches reviews written by this profile from the Reviews Service.",
        responses={200: OpenApiResponse(description="List of reviews")},
    ),
    applications=extend_schema(
        summary="Get Applications by Profile",
        tags=["Profiles (External)"],
        description="Fetches rental applications by this profile from the Application Service.",
        responses={200: OpenApiResponse(description="List of applications")},
    ),
    stats=extend_schema(
        summary="Profile Statistics",
        tags=["Profiles"],
        responses={200: OpenApiResponse(description="Aggregate stats")},
    ),
)
class ProfileViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for user Profiles.

    Custom actions:
        GET    /api/profiles/profiles/{id}/reviews/       → reviews written by this user (from reviews_service)
        GET    /api/profiles/profiles/{id}/applications/   → applications by this user (from application_service)
        GET    /api/profiles/profiles/by-email/?email=X    → lookup profile by email
    """

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_email_verified", "gender"]
    search_fields = ["first_name", "last_name", "email", "userID"]
    ordering_fields = ["created_at", "first_name", "last_name"]
    ordering = ["-created_at"]


    def get_permissions(self):
        if self.action in ["create", "by_email"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProfileListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProfileCreateUpdateSerializer
        return ProfileSerializer

    def perform_create(self, serializer):
        # 1. Save the profile to the database
        profile = serializer.save()

        # 2. Trigger the Celery task to publish the Kafka event
        send_profile_creation_event.delay(
            user_id=str(profile.id),
            email=profile.email,
            first_name=profile.first_name,
            last_name=profile.last_name
        )


    @action(detail=False, methods=["get"], url_path="by-email")
    def by_email(self, request):
        """Lookup a profile by email address."""
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"error": "email query param is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            profile = Profile.objects.get(email=email)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        """
        INTER-SERVICE CALL → reviews_service
        Fetches all reviews written by this profile.
        """
        profile = self.get_object()
        try:
            url = f"{settings.REVIEWS_SERVICE_URL}/api/reviews/reviews/?profile_id={profile.id}"
            resp = make_resilient_request(
                url,
                method="GET",
                service_name="reviews_service",
                max_attempts=3,
                timeout=2,
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {"message": "Reviews service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail=True, methods=["get"])
    def applications(self, request, pk=None):
        """
        INTER-SERVICE CALL → application_service
        Fetches all rental applications by this profile.
        """
        profile = self.get_object()
        try:
            url = f"{settings.LISTINGS_SERVICE_URL}/api/applications/applications/?profile_id={profile.id}"
            resp = make_resilient_request(
                url,
                method="GET",
                service_name="application_service",
                max_attempts=3,
                timeout=2,
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {"message": "Application service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Aggregate profile statistics."""
        queryset = self.get_queryset()
        stats = {
            "total_profiles": queryset.count(),
            "verified_emails": queryset.filter(is_email_verified=True).count(),
            "gender_breakdown": {
                "male": queryset.filter(gender="M").count(),
                "female": queryset.filter(gender="F").count(),
                "other": queryset.filter(gender="O").count(),
                "prefer_not": queryset.filter(gender="P").count(),
            },
        }
        return Response(stats)


@extend_schema_view(
    request_otp=extend_schema(
        summary="Request Email OTP",
        tags=["OTP Verification"],
        description="Generate a secure 6-digit OTP and send via email.",
        responses={200: OpenApiResponse(description="OTP sent successfully")},
    ),
    verify_otp=extend_schema(
        summary="Verify Email OTP",
        tags=["OTP Verification"],
        description="Verify an OTP and mark the profile's email as verified.",
        responses={
            200: OpenApiResponse(description="Email verified successfully"),
            400: OpenApiResponse(description="Invalid or expired OTP"),
        },
    ),
)
class EmailOTPViewSet(viewsets.GenericViewSet):
    """
    ViewSet for OTP management using Redis and Celery.

    Custom actions:
        POST /api/profiles/otp/request_otp/  → generate and store an OTP in Redis, dispatch email Celery task
        POST /api/profiles/otp/verify_otp/   → verify an OTP from Redis and mark email as verified
    """

    serializer_class = EmailOTPRequestSerializer
    permission_classes = [AllowAny]

    def get_throttles(self):
        if self.action == "request_otp":
            return [OTPRequestThrottle()]
        elif self.action == "verify_otp":
            return [OTPVerifyThrottle()]
        return super().get_throttles()

    @action(detail=False, methods=["post"], serializer_class=EmailOTPRequestSerializer)
    def request_otp(self, request):
        """
        Generate a secure 6-digit OTP, hash it, store in Redis for 5 minutes,
        and dispatch a Celery task to send it via email.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()

        # Generate secure 6-digit OTP
        otp = "".join(random.choices(string.digits, k=6))
        otp_hash = make_password(otp)

        redis_key = f"{settings.OTP_REDIS_KEY_PREFIX}:{email}"
        cache.set(redis_key, otp_hash, timeout=settings.OTP_EXPIRY_SECONDS)

        send_otp_email.delay(email, otp)

        return Response(
            {"message": "OTP sent successfully. Please verify your email."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], serializer_class=EmailOTPVerifySerializer)
    def verify_otp(self, request):
        """Verify an OTP from Redis and mark the profile's email as verified."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        otp = serializer.validated_data["otp"].strip()

        redis_key = f"{settings.OTP_REDIS_KEY_PREFIX}:{email}"
        attempts_key = f"otp_attempts:{email}"

        # Check existing attempts
        attempts = cache.get(attempts_key) or 0
        if attempts >= 5:
            cache.delete(redis_key)
            cache.delete(attempts_key)
            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stored_hash = cache.get(redis_key)

        if not stored_hash or not check_password(otp, stored_hash):
            new_attempts = attempts + 1
            cache.set(attempts_key, new_attempts, timeout=settings.OTP_EXPIRY_SECONDS)
            if new_attempts >= 5:
                # Delete OTP as maximum attempts reached
                cache.delete(redis_key)
                cache.delete(attempts_key)
            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark the profile's email as verified
        try:
            profile = Profile.objects.get(email=email)
            profile.is_email_verified = True
            profile.save()
        except Profile.DoesNotExist:
            pass  # OTP verified but no profile yet — that's okay

        cache.delete(redis_key)
        cache.delete(attempts_key)

        return Response(
            {"message": "Email verified successfully"}, status=status.HTTP_200_OK
        )
