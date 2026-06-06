import hashlib
import random
import string

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.conf import settings
import requests

from profiles_app.models import Profile, EmailOTP
from profiles_app.api.serializers import (
    ProfileSerializer,
    ProfileListSerializer,
    ProfileCreateUpdateSerializer,
    EmailOTPSerializer,
    EmailOTPRequestSerializer,
    EmailOTPVerifySerializer,
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
    permission_classes = [AllowAny]
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_email_verified', 'gender']
    search_fields = ['first_name', 'last_name', 'email', 'userID']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProfileCreateUpdateSerializer
        return ProfileSerializer

    @action(detail=False, methods=['get'], url_path='by-email')
    def by_email(self, request):
        """Lookup a profile by email address."""
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'email query param is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = Profile.objects.get(email=email)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """
        INTER-SERVICE CALL → reviews_service
        Fetches all reviews written by this profile.
        """
        profile = self.get_object()
        try:
            url = f"{settings.REVIEWS_SERVICE_URL}/api/reviews/reviews/?profile_id={profile.id}"
            resp = requests.get(url, timeout=5)
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {'error': 'Reviews service is unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """
        INTER-SERVICE CALL → application_service
        Fetches all rental applications by this profile.
        """
        profile = self.get_object()
        try:
            url = f"{settings.LISTINGS_SERVICE_URL}/api/applications/applications/?profile_id={profile.id}"
            resp = requests.get(url, timeout=5)
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {'error': 'Application service is unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Aggregate profile statistics."""
        queryset = self.get_queryset()
        stats = {
            'total_profiles': queryset.count(),
            'verified_emails': queryset.filter(is_email_verified=True).count(),
            'gender_breakdown': {
                'male': queryset.filter(gender='M').count(),
                'female': queryset.filter(gender='F').count(),
                'other': queryset.filter(gender='O').count(),
                'prefer_not': queryset.filter(gender='P').count(),
            },
        }
        return Response(stats)


class EmailOTPViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OTP management.

    Custom actions:
        POST /api/profiles/otp/request_otp/  → generate and store an OTP
        POST /api/profiles/otp/verify_otp/   → verify an OTP and mark email as verified
    """

    queryset = EmailOTP.objects.all()
    serializer_class = EmailOTPSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def request_otp(self, request):
        """
        Generate a 6-digit OTP, hash it, and store it.
        In production, you'd send this OTP via email.
        """
        serializer = EmailOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        # Store with 10-minute expiry
        EmailOTP.objects.create(
            email=email,
            otp_hash=otp_hash,
            expiry_date=timezone.now() + timezone.timedelta(minutes=10),
        )

        # In production: send email here
        # For dev, return the OTP directly
        return Response({
            'message': 'OTP generated successfully',
            'otp': otp,  # Remove this in production!
            'expires_in': '10 minutes',
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify an OTP and mark the associated profile's email as verified."""
        serializer = EmailOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        try:
            otp_record = EmailOTP.objects.filter(
                email=email,
                otp_hash=otp_hash,
                expiry_date__gte=timezone.now(),
            ).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark the profile's email as verified
        try:
            profile = Profile.objects.get(email=email)
            profile.is_email_verified = True
            profile.save()
        except Profile.DoesNotExist:
            pass  # OTP verified but no profile yet — that's okay

        # Delete used OTP
        otp_record.delete()

        return Response({'message': 'Email verified successfully'})
