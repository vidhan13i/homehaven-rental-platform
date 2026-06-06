from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Avg, Count

from listings.models import Listing, Unit, Agent, Images, AgentImages
from listings.api.serializers import (
    # Listing serializers
    ListingSerializer,
    ListingListSerializer,
    ListingCreateUpdateSerializer,
    # Unit serializers
    UnitSerializer,
    UnitListSerializer,
    UnitCreateUpdateSerializer,
    UnitImageSerializer,
    # Agent serializers
    AgentSerializer,
    AgentListSerializer,
    AgentCreateUpdateSerializer,
    AgentImageSerializer,
)
from listings.api.pagination import ListingPagination, StandardResultsSetPagination
from listings.api.filters import (
    ListingFilter,
    AvailableListingFilter,
    UnitFilter,
    AgentFilter,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  LISTING VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class ListingViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Listings.

    Endpoints:
        GET    /api/listings/              → list all listings
        POST   /api/listings/              → create a new listing
        GET    /api/listings/{id}/         → retrieve a listing
        PUT    /api/listings/{id}/         → full update
        PATCH  /api/listings/{id}/         → partial update
        DELETE /api/listings/{id}/         → delete

    Custom actions:
        GET    /api/listings/available/    → only available listings
        GET    /api/listings/verified/     → only verified listings
        GET    /api/listings/stats/        → aggregate statistics
        POST   /api/listings/{id}/verify/  → mark as verified
        POST   /api/listings/{id}/unverify/→ mark as unverified
    """

    queryset = Listing.objects.select_related('unit_ID', 'unit_ID__agent_ID').all()
    permission_classes = [AllowAny]
    serializer_class = ListingSerializer
    pagination_class = ListingPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['rent', 'unit_ID__full_address', 'lease_term']
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
        """Return only listings with available_date in the future."""
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
        """Return only verified listings."""
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
        """Return aggregate statistics for all listings."""
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
        """Mark a listing as verified."""
        listing = self.get_object()
        listing.is_listing_verified = True
        listing.save()
        serializer = self.get_serializer(listing)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unverify(self, request, pk=None):
        """Mark a listing as unverified."""
        listing = self.get_object()
        listing.is_listing_verified = False
        listing.save()
        serializer = self.get_serializer(listing)
        return Response(serializer.data)


class PublicListingListView(generics.ListAPIView):
    """
    Public-facing endpoint for tenants browsing the marketplace.
    Only returns verified, currently available listings.
    """
    queryset = Listing.objects.select_related('unit_ID', 'unit_ID__agent_ID').filter(
        is_listing_verified=True,
        available_date__gte=timezone.now().date()
    )
    serializer_class = ListingListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AvailableListingFilter
    search_fields = ['unit_ID__full_address', 'rent']
    ordering_fields = ['rent', 'available_date', 'publish_date']
    ordering = ['rent']


class PublicListingDetailView(generics.RetrieveAPIView):
    """Public-facing detail view for a single verified listing."""
    queryset = Listing.objects.select_related('unit_ID', 'unit_ID__agent_ID').filter(
        is_listing_verified=True
    )
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class UnitViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Units (apartments/flats inside a building).

    Endpoints:
        GET    /api/units/                → list all units
        POST   /api/units/                → create a new unit
        GET    /api/units/{id}/           → retrieve a unit (with images)
        PUT    /api/units/{id}/           → full update
        PATCH  /api/units/{id}/           → partial update
        DELETE /api/units/{id}/           → delete

    Custom actions:
        GET    /api/units/{id}/listings/  → get all listings for this unit
        GET    /api/units/{id}/images/    → get all images for this unit
        POST   /api/units/{id}/add_image/ → add an image to this unit
    """

    queryset = Unit.objects.select_related('agent_ID').prefetch_related('images').all()
    permission_classes = [AllowAny]
    serializer_class = UnitSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UnitFilter
    search_fields = ['full_address', 'unit_no', 'description']
    ordering_fields = ['created_at', 'no_bedrooms', 'no_bathrooms']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return UnitListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return UnitCreateUpdateSerializer
        return UnitSerializer

    @action(detail=True, methods=['get'])
    def listings(self, request, pk=None):
        """Get all listings attached to this unit."""
        unit = self.get_object()
        listings = unit.Listings.all()
        serializer = ListingListSerializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get all images for this unit."""
        unit = self.get_object()
        images = unit.images.all()
        serializer = UnitImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """
        Add an image to this unit.
        POST body: { "image_url": "https://..." }
        """
        unit = self.get_object()
        serializer = UnitImageSerializer(data={
            'image_url': request.data.get('image_url'),
            'unit_ID': unit.id,
        })
        serializer.is_valid(raise_exception=True)

        # Manually create since UnitImageSerializer doesn't include unit_ID for create
        Images.objects.create(
            image_url=request.data['image_url'],
            unit_ID=unit,
        )
        return Response(
            {'message': 'Image added successfully'},
            status=status.HTTP_201_CREATED
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENT VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class AgentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Agents (property managers / real estate agents).

    Endpoints:
        GET    /api/agents/                  → list all agents
        POST   /api/agents/                  → register a new agent
        GET    /api/agents/{id}/             → agent details (with images & unit count)
        PUT    /api/agents/{id}/             → full update
        PATCH  /api/agents/{id}/             → partial update
        DELETE /api/agents/{id}/             → delete

    Custom actions:
        GET    /api/agents/{id}/units/       → all units managed by this agent
        GET    /api/agents/{id}/listings/    → all listings by this agent
        POST   /api/agents/{id}/verify/      → verify this agent
        POST   /api/agents/{id}/add_image/   → add a profile image
        GET    /api/agents/verified/          → only verified agents
        GET    /api/agents/stats/             → aggregate stats
    """

    queryset = Agent.objects.prefetch_related('units', 'agentimages_set').all()
    permission_classes = [AllowAny]
    serializer_class = AgentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AgentFilter
    search_fields = ['first_name', 'last_name', 'email', 'agent_organization']
    ordering_fields = ['created_at', 'agent_experience', 'first_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AgentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AgentCreateUpdateSerializer
        return AgentSerializer

    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        """Get all units managed by this agent."""
        agent = self.get_object()
        units = agent.units.all()
        serializer = UnitListSerializer(units, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def listings(self, request, pk=None):
        """Get all listings across all units managed by this agent."""
        agent = self.get_object()
        listings = Listing.objects.filter(unit_ID__agent_ID=agent)
        serializer = ListingListSerializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Mark an agent as verified."""
        agent = self.get_object()
        agent.is_agent_verified = True
        agent.save()
        serializer = self.get_serializer(agent)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """
        Add a profile/document image to this agent.
        POST body: { "agent_image_url": "https://..." }
        """
        agent = self.get_object()
        image_url = request.data.get('agent_image_url')
        if not image_url:
            return Response(
                {'error': 'agent_image_url is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        AgentImages.objects.create(
            agent_image_url=image_url,
            agent_ID=agent,
        )
        return Response(
            {'message': 'Image added successfully'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def verified(self, request):
        """Return only verified agents."""
        queryset = self.get_queryset().filter(is_agent_verified=True)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AgentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AgentListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return aggregate statistics for agents."""
        queryset = self.get_queryset()
        stats = {
            'total_agents': queryset.count(),
            'verified_agents': queryset.filter(is_agent_verified=True).count(),
            'average_experience': queryset.aggregate(
                Avg('agent_experience')
            )['agent_experience__avg'],
            'top_organizations': list(
                queryset.values('agent_organization')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
        }
        return Response(stats)


# ═══════════════════════════════════════════════════════════════════════════════
#  IMAGE VIEWS (standalone CRUD for bulk operations)
# ═══════════════════════════════════════════════════════════════════════════════

class UnitImageViewSet(viewsets.ModelViewSet):
    """
    Standalone CRUD for unit images.
    Use this for bulk image management. For adding images to a specific
    unit, prefer the /api/units/{id}/add_image/ action instead.
    """
    queryset = Images.objects.select_related('unit_ID').all()
    serializer_class = UnitImageSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['unit_ID']


class AgentImageViewSet(viewsets.ModelViewSet):
    """
    Standalone CRUD for agent images.
    Use this for bulk image management. For adding images to a specific
    agent, prefer the /api/agents/{id}/add_image/ action instead.
    """
    queryset = AgentImages.objects.select_related('agent_ID').all()
    serializer_class = AgentImageSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent_ID']