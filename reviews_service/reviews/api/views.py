from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q
from django.conf import settings
import requests
from shared_lib.resilience import make_resilient_request

from reviews.models.reviews import Review
from reviews.api.serializers import (
    ReviewSerializer,
    ReviewListSerializer,
    ReviewCreateUpdateSerializer,
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Reviews.

    Custom actions:
        GET  /api/reviews/reviews/by-building/?building_id=X   → reviews for a building
        GET  /api/reviews/reviews/by-profile/?profile_id=X     → reviews by a user
        GET  /api/reviews/reviews/{id}/building/               → fetch building details (inter-service)
        GET  /api/reviews/reviews/{id}/author/                 → fetch author profile (inter-service)
        GET  /api/reviews/reviews/stats/                       → aggregate statistics
        GET  /api/reviews/reviews/building-summary/?building_id=X → rating breakdown for a building
        POST /api/reviews/reviews/{id}/submit/                 → submit a draft review
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'by_building', 'by_profile', 'building', 'author', 'stats', 'building_summary']:
            return [AllowAny()]
        return [IsAuthenticated()]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['building_ID', 'profile_ID', 'status', 'is_pet_friendly', 'is_received_deposit']
    search_fields = ['Title', 'Pros', 'Cons', 'Advice', 'full_address']
    ordering_fields = ['review_date', 'created_at', 'cleanliness_rating', 'starting_rent']
    ordering = ['-review_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    # ── Lookup endpoints ───────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='by-building')
    def by_building(self, request):
        """Get all reviews for a specific building (UUID from building_service)."""
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        reviews = self.get_queryset().filter(building_ID=building_id, status='SUBMITTED')
        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-profile')
    def by_profile(self, request):
        """Get all reviews written by a specific user (UUID from profile_service)."""
        profile_id = request.query_params.get('profile_id')
        if not profile_id:
            return Response({'error': 'profile_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        reviews = self.get_queryset().filter(profile_ID=profile_id)
        serializer = ReviewListSerializer(reviews, many=True)
        return Response(serializer.data)

    # ── Inter-service calls ────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def building(self, request, pk=None):
        """
        INTER-SERVICE CALL → building_service
        Fetch the building details for this review.
        """
        review = self.get_object()
        try:
            url = f"{settings.BUILDING_SERVICE_URL}/api/buildings/buildings/{review.building_ID}/"
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

    @action(detail=True, methods=['get'])
    def author(self, request, pk=None):
        """
        INTER-SERVICE CALL → profile_service
        Fetch the profile of the person who wrote this review.
        """
        review = self.get_object()
        try:
            url = f"{settings.PROFILE_SERVICE_URL}/api/profiles/profiles/{review.profile_ID}/"
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

    # ── Workflow ───────────────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft/in-progress review."""
        review = self.get_object()
        if review.status == 'SUBMITTED':
            return Response({'error': 'Review already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        review.status = Review.Status.SUBMITTED
        review.save()
        return Response(ReviewSerializer(review).data)

    # ── Analytics ──────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Global review statistics."""
        qs = self.get_queryset().filter(status='SUBMITTED')
        stats = {
            'total_reviews': qs.count(),
            'avg_cleanliness': qs.aggregate(Avg('cleanliness_rating'))['cleanliness_rating__avg'],
            'avg_garbage': qs.aggregate(Avg('garbage_management_rating'))['garbage_management_rating__avg'],
            'avg_neighbours': qs.aggregate(Avg('neighbours_rating'))['neighbours_rating__avg'],
            'avg_water': qs.aggregate(Avg('water_supply_rating'))['water_supply_rating__avg'],
            'avg_maintenance': qs.aggregate(Avg('building_maintenance_rating'))['building_maintenance_rating__avg'],
            'deposit_return_rate': (
                qs.filter(is_received_deposit=True).count() / max(qs.count(), 1) * 100
            ),
            'pet_friendly_pct': (
                qs.filter(is_pet_friendly=True).count() / max(qs.count(), 1) * 100
            ),
        }
        return Response(stats)

    @action(detail=False, methods=['get'], url_path='building-summary')
    def building_summary(self, request):
        """
        Get a complete rating breakdown for a specific building.
        Used by the frontend to show the building's review summary card.
        """
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        reviews = self.get_queryset().filter(building_ID=building_id, status='SUBMITTED')

        if not reviews.exists():
            return Response({'error': 'No reviews found for this building'}, status=status.HTTP_404_NOT_FOUND)

        summary = reviews.aggregate(
            avg_cleanliness=Avg('cleanliness_rating'),
            avg_garbage=Avg('garbage_management_rating'),
            avg_neighbours=Avg('neighbours_rating'),
            avg_water=Avg('water_supply_rating'),
            avg_maintenance=Avg('building_maintenance_rating'),
            avg_starting_rent=Avg('starting_rent'),
            avg_ending_rent=Avg('ending_rent'),
            total_reviews=Count('id'),
        )

        # Overall average
        rating_fields = ['avg_cleanliness', 'avg_garbage', 'avg_neighbours', 'avg_water', 'avg_maintenance']
        ratings = [summary[f] for f in rating_fields if summary[f] is not None]
        summary['overall_avg'] = round(sum(ratings) / len(ratings), 2) if ratings else None

        summary['deposit_return_rate'] = (
            reviews.filter(is_received_deposit=True).count() / max(reviews.count(), 1) * 100
        )
        summary['pet_friendly_pct'] = (
            reviews.filter(is_pet_friendly=True).count() / max(reviews.count(), 1) * 100
        )

        return Response(summary)
