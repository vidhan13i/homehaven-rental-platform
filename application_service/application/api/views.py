import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Count
import requests
from shared_lib.resilience import make_resilient_request
from shared_lib.kafka.producer import KafkaEventProducer
from shared_lib.kafka.events import build_event
from shared_lib.kafka.topics import Topics

logger = logging.getLogger("application.views")
_kafka_producer = KafkaEventProducer()

from application.models import Application, Applicant, Document
from application.api.serializers import (
    ApplicationSerializer,
    ApplicationListSerializer,
    ApplicationCreateSerializer,
    ApplicantSerializer,
    ApplicantListSerializer,
    ApplicantCreateUpdateSerializer,
    DocumentSerializer,
)


from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample

@extend_schema_view(
    list=extend_schema(summary="List Applications", tags=["Applications"]),
    retrieve=extend_schema(summary="Retrieve Application", tags=["Applications"]),
    create=extend_schema(summary="Create Application", tags=["Applications"], examples=[OpenApiExample("Create App", value={"status": "pending"}, request_only=True)]),
    update=extend_schema(summary="Update Application", tags=["Applications"]),
    partial_update=extend_schema(summary="Partially Update Application", tags=["Applications"]),
    destroy=extend_schema(summary="Delete Application", tags=["Applications"]),
    approve=extend_schema(summary="Approve Application", tags=["Applications"]),
    reject=extend_schema(summary="Reject Application", tags=["Applications"])
)
class ApplicationViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for rental Applications.

    Custom actions:
        POST /api/applications/applications/{id}/approve/   → approve
        POST /api/applications/applications/{id}/reject/    → reject
        GET  /api/applications/applications/by-building/?building_id=X
        GET  /api/applications/applications/by-unit/?unit_id=X
        GET  /api/applications/applications/{id}/listing/   → fetch listing from listings_service
        GET  /api/applications/applications/stats/
    """

    queryset = Application.objects.select_related('applicant_ID').all()
    permission_classes = [IsAuthenticated]
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        return self.queryset.filter(applicant_ID__profile_ID=self.request.user.id)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application_status', 'building_ID', 'unit_ID']
    ordering_fields = ['submitted_at_date', 'created_at', 'application_status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a rental application."""
        from django.shortcuts import get_object_or_404
        application = get_object_or_404(Application, pk=pk)
        application.application_status = Application.ApplicationStatus.APPROVED
        application.save()
        # Publish ApplicationApproved event — notification_service and chat_service consume this
        _publish_application_event(
            "ApplicationApproved",
            Topics.APPLICATIONS_APPROVED,
            application,
            actor_id=str(request.user.id),
        )
        return Response(ApplicationSerializer(application).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a rental application."""
        from django.shortcuts import get_object_or_404
        application = get_object_or_404(Application, pk=pk)
        application.application_status = Application.ApplicationStatus.REJECTED
        application.save()
        # Publish ApplicationRejected event
        _publish_application_event(
            "ApplicationRejected",
            Topics.APPLICATIONS_REJECTED,
            application,
            actor_id=str(request.user.id),
        )
        return Response(ApplicationSerializer(application).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft application for review."""
        application = self.get_object()
        if application.application_status != Application.ApplicationStatus.DRAFT:
            return Response(
                {'error': 'Only draft applications can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        application.application_status = Application.ApplicationStatus.SUBMITTED
        application.save()
        return Response(ApplicationSerializer(application).data)

    @action(detail=False, methods=['get'], url_path='by-building')
    def by_building(self, request):
        """Get all applications for a specific building (UUID from building_service)."""
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        apps = Application.objects.all().filter(building_ID=building_id)
        serializer = ApplicationListSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-unit')
    def by_unit(self, request):
        """Get all applications for a specific unit (UUID from listings_service)."""
        unit_id = request.query_params.get('unit_id')
        if not unit_id:
            return Response({'error': 'unit_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        apps = Application.objects.all().filter(unit_ID=unit_id)
        serializer = ApplicationListSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def listing(self, request, pk=None):
        """
        INTER-SERVICE CALL → listings_service
        Fetch the listing details for this application's unit.
        """
        application = self.get_object()
        try:
            url = f"{settings.LISTINGS_SERVICE_URL}/api/listings/units/{application.unit_ID}/"
            resp = make_resilient_request(
                url,
                method='GET',
                service_name='listings_service',
                max_attempts=3,
                timeout=2,
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {"message": "Listings service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=True, methods=['get'])
    def building(self, request, pk=None):
        """
        INTER-SERVICE CALL → building_service
        Fetch the building details for this application.
        """
        application = self.get_object()
        try:
            url = f"{settings.BUILDING_SERVICE_URL}/api/buildings/buildings/{application.building_ID}/"
            resp = make_resilient_request(
                url,
                method='GET',
                service_name='building_service',
                max_attempts=3,
                timeout=2,
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {"message": "Building service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Application statistics for admin dashboard."""
        qs = self.get_queryset()
        stats = {
            'total': qs.count(),
            'draft': qs.filter(application_status='draft').count(),
            'submitted': qs.filter(application_status='submitted').count(),
            'approved': qs.filter(application_status='approved').count(),
            'rejected': qs.filter(application_status='rejected').count(),
            'top_buildings': list(
                qs.values('building_ID')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
        }
        return Response(stats)


class ApplicantViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Applicants (tenant profiles applying for rentals).

    Custom actions:
        GET /api/applications/applicants/{id}/applications/  → all applications by this person
        GET /api/applications/applicants/{id}/documents/      → all uploaded documents
        GET /api/applications/applicants/{id}/profile/         → fetch from profile_service
    """

    queryset = Applicant.objects.prefetch_related('document', 'application').all()
    permission_classes = [IsAuthenticated]
    serializer_class = ApplicantSerializer

    def get_queryset(self):
        return self.queryset.filter(profile_ID=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(profile_ID=self.request.user.id)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['has_rented_before', 'marital_status']
    search_fields = ['employer', 'job_title']
    ordering_fields = ['created_at', 'credit_score', 'income']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicantListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ApplicantCreateUpdateSerializer
        return ApplicantSerializer

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Get all applications submitted by this applicant."""
        applicant = self.get_object()
        apps = applicant.application.all()
        serializer = ApplicationListSerializer(apps, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents uploaded by this applicant."""
        applicant = self.get_object()
        docs = applicant.document.all()
        serializer = DocumentSerializer(docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """
        INTER-SERVICE CALL → profile_service
        Fetch the full profile for this applicant.
        """
        applicant = self.get_object()
        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/{applicant.profile_ID}/"
            resp = make_resilient_request(
                url,
                method='GET',
                service_name='profile_service',
                max_attempts=3,
                timeout=2,
            )
            return Response(resp.json(), status=resp.status_code)
        except requests.exceptions.RequestException:
            return Response(
                {"message": "Profile service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for applicant documents (ID proofs, bank statements, etc.)."""
    queryset = Document.objects.select_related('applicant_ID').all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(applicant_ID__profile_ID=self.request.user.id)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['applicant_ID']

    def create(self, request, *args, **kwargs):
        print("REQUEST DATA:", request.data)
        print("REQUEST FILES:", request.FILES)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("VALIDATION ERRORS:", serializer.errors)
        return super().create(request, *args, **kwargs)


def _publish_application_event(
    event_type: str,
    topic: str,
    application,
    actor_id: str = None,
) -> None:
    """
    Publish a domain event for an application state change.
    Never raises — Kafka failures must never block the API response.
    """
    try:
        applicant = getattr(application, 'applicant_ID', None)
        event = build_event(
            event_type=event_type,
            aggregate_id=str(application.id),
            source_service="application_service",
            payload={
                "application_id": str(application.id),
                "application_status": application.application_status,
                "unit_id": str(application.unit_ID) if application.unit_ID else None,
                "building_id": str(application.building_ID) if application.building_ID else None,
                "renter_id": str(applicant.profile_ID) if applicant else None,
                "agent_id": actor_id,
            },
        )
        _kafka_producer.publish(topic, event, key=str(application.id))
    except Exception as exc:
        logger.error(
            "Failed to publish %s event for application %s: %s",
            event_type, application.id, exc
        )
