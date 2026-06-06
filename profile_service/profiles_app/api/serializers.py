from rest_framework import serializers
from profiles_app.models import Profile, EmailOTP


class ProfileSerializer(serializers.ModelSerializer):
    """Full profile detail serializer."""
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'userID', 'first_name', 'last_name', 'full_name',
            'email', 'DOB', 'phone_number',
            'gender', 'gender_display', 'ethnicity',
            'is_email_verified',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class ProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for profile lists."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'userID', 'full_name', 'email',
            'phone_number', 'is_email_verified',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class ProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating profiles with validation."""

    class Meta:
        model = Profile
        fields = [
            'userID', 'first_name', 'last_name', 'email',
            'DOB', 'phone_number', 'gender', 'ethnicity',
        ]

    def validate_phone_number(self, value):
        if value is not None and len(str(value)) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

    def validate_email(self, value):
        # Check uniqueness on create
        if self.instance is None:  # Creating
            if Profile.objects.filter(email=value).exists():
                raise serializers.ValidationError("A profile with this email already exists")
        return value


class EmailOTPSerializer(serializers.ModelSerializer):
    """Serializer for OTP records."""

    class Meta:
        model = EmailOTP
        fields = ['id', 'email', 'otp_hash', 'expiry_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class EmailOTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting a new OTP (input only)."""
    email = serializers.EmailField()


class EmailOTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying an OTP (input only)."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
