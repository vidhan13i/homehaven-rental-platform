from rest_framework import viewsets, generics, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Avg

from listings.models import Listing
from listings.api.serializers import (
    ListingSerializer,
    ListingListSerializer,
    ListingCreateUpdateSerializer
)
from listings.api.pagination import ListingPagination, StandardResultsSetPagination
from listings.api.filters import ListingFilter, AvailableListingFilter


class ListingViewSet(viewsets.ModelViewSet):

    queryset = Listing.objects.select_related('unit_ID').all()
    permission_classes = [AllowAny]
    serializer_class = ListingSerializer
    pagination_class = ListingPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['rent', 'unit_ID__address', 'lease_term']
    ordering_fields = ['rent', 'available_date', 'publish_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):

        if self.action == 'list':
            return ListingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ListingCreateUpdateSerializer
        return ListingSerializer

    def get_queryset(self):

        queryset = super().get_queryset()

        verified = self.request.query_params.get('verified', None)
        if verified is not None:
            queryset = queryset.filter(is_listing_verified=verified.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'])
    def available(self, request):
        queryset = self.get_queryset().filter(
            available_date__gte=timezone.now().date()
        )

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ListingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def verified(self, request):

        queryset = self.get_queryset().filter(is_listing_verified=True)


        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ListingListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ListingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):

        queryset = self.get_queryset()

        stats = {
            'total_listings': queryset.count(),
            'verified_listings': queryset.filter(is_listing_verified=True).count(),
            'available_listings': queryset.filter(
                available_date__gte=timezone.now().date()
            ).count(),
            'average_rent': queryset.aggregate(Avg('rent'))['rent__avg'],
            'average_deposit': queryset.aggregate(Avg('deposit_amount'))['deposit_amount__avg'],
            'average_lease_term': queryset.aggregate(Avg('lease_term'))['lease_term__avg'],
        }

        return Response(stats)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):

        listing = self.get_object()
        listing.is_listing_verified = True
        listing.save()
        serializer = self.get_serializer(listing)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):

        listing = self.get_object()
        listing.is_listing_verified = False
        listing.save()
        serializer = self.get_serializer(listing)
        return Response(serializer.data)


class PublicListingListView(generics.ListAPIView):

    queryset = Listing.objects.select_related('unit_ID').filter(
        is_listing_verified=True,
        available_date__gte=timezone.now().date()
    )
    serializer_class = ListingListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AvailableListingFilter
    search_fields = ['unit_ID__address', 'rent']
    ordering_fields = ['rent', 'available_date', 'publish_date']
    ordering = ['rent']


class PublicListingDetailView(generics.RetrieveAPIView):
    queryset = Listing.objects.select_related('unit_ID').filter(
        is_listing_verified=True
    )
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]