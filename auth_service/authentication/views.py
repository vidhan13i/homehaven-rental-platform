import requests
from django.conf import settings
from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, UserSerializer
from .models import User
from shared_lib.resilience import make_resilient_request

class ServiceUnavailable(exceptions.APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Profile service temporarily unavailable'
    default_code = 'service_unavailable'


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Step 1: Create Profile in profile_service
        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/"
            profile_payload = {
                "id": str(user.id),
                "userID": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "DOB": "2000-01-01",  # default DOB required by profile service
                "gender": "P",        # default choices ('P' for Prefer Not to Say)
                "is_email_verified": False
            }
            resp = make_resilient_request(
                url,
                method='POST',
                service_name='profile_service',
                max_attempts=2,
                timeout=2,
                json=profile_payload,
                headers={"Host": "localhost"}
            )
            if resp.status_code not in [200, 201]:
                user.delete()
                return Response(
                    {"error": f"Failed to create profile. Registration rolled back. Detail: {resp.text}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except requests.exceptions.RequestException:
            user.delete()
            return Response(
                {"message": "Profile service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Step 2: Request OTP automatically
        try:
            otp_url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/otp/request_otp/"
            make_resilient_request(
                otp_url,
                method='POST',
                service_name='profile_service',
                max_attempts=2,
                timeout=2,
                json={"email": user.email},
                headers={"Host": "localhost"}
            )
        except requests.exceptions.RequestException:
            user.delete()
            return Response(
                {"message": "OTP service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({
            "message": "OTP sent successfully. Please verify your email."
        }, status=status.HTTP_201_CREATED)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        # Authenticate credentials using standard simplejwt logic
        data = super().validate(attrs)

        # Check OTP verification status in profile service
        email = self.user.email
        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/by-email/?email={email}"
            resp = make_resilient_request(
                url,
                method='GET',
                service_name='profile_service',
                max_attempts=2,
                timeout=2,
                headers={"Host": "localhost"}
            )
            if resp.status_code == 200:
                profile_data = resp.json()
                if not profile_data.get('is_email_verified', False):
                    raise exceptions.ValidationError("Email not verified. Please verify your OTP.")
            elif resp.status_code == 404:
                raise exceptions.ValidationError("Profile not found. Registration might be incomplete.")
            else:
                raise exceptions.ValidationError("Unable to verify profile verification status.")
        except requests.exceptions.RequestException:
            raise ServiceUnavailable()

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ServiceUnavailable:
            return Response(
                {"message": "Profile service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
