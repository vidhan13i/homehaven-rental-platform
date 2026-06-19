import requests
from django.conf import settings
from rest_framework import status, generics, exceptions
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, UserSerializer
from .models import User

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Step 1: Create Profile in profile_service
        profile_created = False
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
            resp = requests.post(url, json=profile_payload, headers={"Host": "localhost"}, timeout=5)
            if resp.status_code in [200, 201]:
                profile_created = True
            else:
                resp_text = resp.text
        except requests.exceptions.RequestException:
            resp_text = "Profile service connection timeout"

        # Rollback user creation to maintain consistency across services
        if not profile_created:
            user.delete()
            return Response(
                {"error": f"Failed to create profile. Registration rolled back. Detail: {resp_text}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 2: Request OTP automatically
        try:
            otp_url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/otp/request_otp/"
            requests.post(otp_url, json={"email": user.email}, headers={"Host": "localhost"}, timeout=5)
        except requests.exceptions.RequestException:
            pass

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
            resp = requests.get(url, headers={"Host": "localhost"}, timeout=5)
            if resp.status_code == 200:
                profile_data = resp.json()
                if not profile_data.get('is_email_verified', False):
                    raise exceptions.ValidationError("Email not verified. Please verify your OTP.")
            elif resp.status_code == 404:
                raise exceptions.ValidationError("Profile not found. Registration might be incomplete.")
            else:
                raise exceptions.ValidationError("Unable to verify profile verification status.")
        except requests.exceptions.RequestException:
            raise exceptions.ValidationError("Profile service is currently unavailable. Please try again later.")

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
