from rest_framework import serializers
from application.models import Application, Applicant, Document


# ─── DOCUMENT SERIALIZERS ─────────────────────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'label', 'file_field', 'applicant_ID', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── APPLICANT SERIALIZERS ────────────────────────────────────────────────────

class ApplicantSerializer(serializers.ModelSerializer):
    """Full applicant detail with nested documents."""
    documents = DocumentSerializer(source='document', many=True, read_only=True)
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Applicant
        fields = [
            'id', 'profile_ID',
            'employer', 'job_title', 'job_start_date',
            'credit_score', 'income', 'savings',
            'expected_movein_date', 'reason',
            'has_rented_before', 'rental_history',
            'marital_status', 'children', 'emergency_info',
            'documents', 'application_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'profile_ID', 'created_at', 'updated_at']

    def get_application_count(self, obj):
        return obj.application.count()


class ApplicantListSerializer(serializers.ModelSerializer):
    """Lightweight applicant list."""
    class Meta:
        model = Applicant
        fields = [
            'id', 'profile_ID', 'employer', 'job_title',
            'credit_score', 'income', 'has_rented_before',
        ]


class ApplicantCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = [
            'employer', 'job_title', 'job_start_date',
            'credit_score', 'income', 'savings',
            'expected_movein_date', 'reason',
            'has_rented_before', 'rental_history',
            'marital_status', 'children', 'emergency_info',
        ]

    def validate_credit_score(self, value):
        if value is not None and (value < 300 or value > 900):
            raise serializers.ValidationError("Credit score must be between 300 and 900")
        return value

    def validate_income(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Income cannot be negative")
        return value


# ─── APPLICATION SERIALIZERS ──────────────────────────────────────────────────

class ApplicationSerializer(serializers.ModelSerializer):
    """Full application detail with nested applicant info."""
    applicant_details = ApplicantSerializer(source='applicant_ID', read_only=True)
    status_display = serializers.CharField(source='get_application_status_display', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'unit_ID', 'building_ID',
            'applicant_ID', 'applicant_details',
            'submitted_at_date', 'lease_term',
            'resident_info',
            'application_status', 'status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'submitted_at_date', 'created_at', 'updated_at']


class ApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight application list for dashboard views."""
    status_display = serializers.CharField(source='get_application_status_display', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'unit_ID', 'building_ID',
            'applicant_ID', 'submitted_at_date',
            'application_status', 'status_display',
        ]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications."""
    class Meta:
        model = Application
        fields = [
            'unit_ID', 'building_ID', 'applicant_ID',
            'lease_term', 'resident_info',
        ]
