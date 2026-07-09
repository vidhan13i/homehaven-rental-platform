import logging
import requests
from django.conf import settings
from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)
from .serializers import RegisterSerializer
from shared_lib.resilience import make_resilient_request
from shared_lib.kafka.producer import KafkaEventProducer
from shared_lib.kafka.events import build_event
from shared_lib.kafka.topics import Topics

logger = logging.getLogger("auth.views")
_kafka_producer = KafkaEventProducer()


class ServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Profile service temporarily unavailable"
    default_code = "service_unavailable"


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Creates a new user account, initializes their profile in the Profile Service, and triggers an OTP verification email.",
        tags=["Authentication"],
        responses={
            201: OpenApiResponse(
                description="OTP sent successfully. Please verify your email."
            ),
            400: OpenApiResponse(
                description="Bad Request - Invalid payload or Profile creation failed"
            ),
            503: OpenApiResponse(
                description="Service Unavailable - Profile or OTP service down"
            ),
        },
        examples=[
            OpenApiExample(
                "Valid Registration",
                summary="Successful registration",
                description="A correct payload to register a new tenant or owner.",
                value={
                    "username": "johndoe",
                    "password": "SecurePassword123!",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                request_only=True,
            )
        ],
    )
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/"
            profile_payload = {
                "id": str(user.id),
                "userID": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "DOB": "2000-01-01",
                "gender": "P",
                "is_email_verified": False,
            }
            resp = make_resilient_request(
                url,
                method="POST",
                service_name="profile_service",
                max_attempts=2,
                timeout=2,
                json=profile_payload,
                headers={"Host": "localhost"},
            )
            if resp.status_code not in [200, 201]:
                user.delete()
                return Response(
                    {
                        "error": f"Failed to create profile. Registration rolled back. Detail: {resp.text}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except requests.exceptions.RequestException:
            user.delete()
            return Response(
                {"message": "Profile service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            otp_url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/otp/request_otp/"
            make_resilient_request(
                otp_url,
                method="POST",
                service_name="profile_service",
                max_attempts=2,
                timeout=2,
                json={"email": user.email},
                headers={"Host": "localhost"},
            )
        except requests.exceptions.RequestException:
            user.delete()
            return Response(
                {"message": "OTP service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        self._publish_user_registered(user)
        return Response(
            {"message": "OTP sent successfully. Please verify your email."},
            status=status.HTTP_201_CREATED,
        )

    def _publish_user_registered(self, user) -> None:
        """Publish UserRegistered domain event to Kafka (fire-and-forget)."""
        try:
            event = build_event(
                event_type="UserRegistered",
                aggregate_id=str(user.id),
                source_service="auth_service",
                payload={
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            )
            _kafka_producer.publish_async(
                Topics.AUTH_USER_REGISTERED,
                event,
                key=str(user.id),
            )
        except Exception as exc:
            logger.error("Failed to publish UserRegistered event: %s", exc)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):

        data = super().validate(attrs)

        email = self.user.email
        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/by-email/?email={email}"
            resp = make_resilient_request(
                url,
                method="GET",
                service_name="profile_service",
                max_attempts=2,
                timeout=2,
                headers={"Host": "localhost"},
            )
            if resp.status_code == 200:
                profile_data = resp.json()
                if not profile_data.get("is_email_verified", False):
                    raise exceptions.ValidationError(
                        "Email not verified. Please verify your OTP."
                    )
            elif resp.status_code == 404:
                raise exceptions.ValidationError(
                    "Profile not found. Registration might be incomplete."
                )
            else:
                raise exceptions.ValidationError(
                    "Unable to verify profile verification status."
                )
        except requests.exceptions.RequestException:
            raise ServiceUnavailable()

        return data


@extend_schema_view(
    post=extend_schema(
        summary="Obtain JWT Token",
        description="Authenticates the user and returns an access and refresh token. Fails if the user's email has not been verified via OTP.",
        tags=["Authentication"],
        responses={
            200: OpenApiResponse(description="Tokens returned successfully"),
            400: OpenApiResponse(description="Email not verified or Profile not found"),
            401: OpenApiResponse(
                description="No active account found with the given credentials"
            ),
            503: OpenApiResponse(description="Profile service temporarily unavailable"),
        },
        examples=[
            OpenApiExample(
                "Login Payload",
                value={"username": "johndoe", "password": "SecurePassword123!"},
                request_only=True,
            )
        ],
    )
)
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ServiceUnavailable:
            return Response(
                {"message": "Profile service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
@extend_schema(
    summary="Validate JWT Token",
    description="Checks if the provided Bearer token is valid and returns the associated user information.",
    tags=["Authentication"],
    responses={
        200: OpenApiResponse(description="Token is valid"),
        401: OpenApiResponse(description="Token is invalid or expired")
    }
)
class ValidateTokenView(APIView):
    # This automatically rejects requests without a valid token (401 Unauthorized)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # If the code reaches here, the token is valid!
        return Response(
            {
                "valid": True,
                "user": {
                    "username": request.user.username,
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )