from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count

from building.models import Building, Images
from building.api.serializers import (
    BuildingSerializer,
    BuildingListSerializer,
    BuildingCreateUpdateSerializer,
    BuildingNearbySerializer,
    BuildingImageSerializer,
)
from building.api.pagination import StandardResultsSetPagination
from building.api.filters import BuildingFilter

# Building views

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)


@extend_schema_view(
    list=extend_schema(summary="List all Buildings", tags=["Buildings"]),
    retrieve=extend_schema(summary="Retrieve a Building", tags=["Buildings"]),
    create=extend_schema(
        summary="Create a Building",
        tags=["Buildings"],
        responses={201: OpenApiResponse(description="Created")},
        examples=[
            OpenApiExample(
                "Create Building", value={"name": "Empire State"}, request_only=True
            )
        ],
    ),
    update=extend_schema(summary="Update a Building", tags=["Buildings"]),
    partial_update=extend_schema(
        summary="Partially Update a Building", tags=["Buildings"]
    ),
    destroy=extend_schema(summary="Delete a Building", tags=["Buildings"]),
    upload_images=extend_schema(summary="Upload Building Images", tags=["Buildings"]),
)
class BuildingViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for Buildings.

    Endpoints:
        GET    /api/buildings/                  → list all buildings
        POST   /api/buildings/                  → create a new building
        GET    /api/buildings/{id}/             → building detail (with images)
        PUT    /api/buildings/{id}/             → full update
        PATCH  /api/buildings/{id}/             → partial update
        DELETE /api/buildings/{id}/             → delete

    Custom actions:
        GET    /api/buildings/stats/            → aggregate statistics
        GET    /api/buildings/cities/           → unique city list
        GET    /api/buildings/nearby/           → geo-based nearby buildings
        GET    /api/buildings/top-rated/        → highest rated buildings
        GET    /api/buildings/{id}/images/      → all images for building
        POST   /api/buildings/{id}/add_image/   → add image to building
    """

    queryset = Building.objects.prefetch_related("images_set").all()
    serializer_class = BuildingSerializer

    def get_permissions(self):
        if self.action in [
            "list",
            "retrieve",
            "stats",
            "cities",
            "nearby",
            "top_rated",
            "images",
        ]:
            return [AllowAny()]
        return [IsAuthenticated()]

    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = BuildingFilter
    search_fields = ["name", "address", "city", "state"]
    ordering_fields = [
        "created_at",
        "avg_rating",
        "review_count",
        "name",
        "no_of_floors",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return BuildingListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return BuildingCreateUpdateSerializer
        elif self.action in ["nearby", "top_rated"]:
            return BuildingNearbySerializer
        return BuildingSerializer

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Returns aggregate statistics across all buildings.
        Useful for an admin dashboard.
        """
        queryset = self.filter_queryset(self.get_queryset())
        stats = {
            "total_buildings": queryset.count(),
            "rera_verified": queryset.filter(is_RERA_verified=True).count(),
            "average_rating": queryset.aggregate(Avg("avg_rating"))["avg_rating__avg"],
            "average_floors": queryset.aggregate(Avg("no_of_floors"))[
                "no_of_floors__avg"
            ],
            "total_units": queryset.aggregate(total=Count("no_of_units"))["total"],
            "buildings_with_gym": queryset.filter(is_gym=True).count(),
            "buildings_with_pool": queryset.filter(is_swimming=True).count(),
            "buildings_with_elevator": queryset.filter(is_elevator=True).count(),
            "top_cities": list(
                queryset.values("city")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
        }
        return Response(stats)

    @action(detail=False, methods=["get"])
    def cities(self, request):
        """
        Returns a list of all unique cities that have buildings.
        Useful for populating a city dropdown/filter on the frontend.
        """
        cities = (
            Building.objects.values("city", "state")
            .annotate(building_count=Count("id"))
            .order_by("-building_count")
        )
        return Response(list(cities))

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """
        Returns buildings near a given lat/lng coordinate.

        Query params:
            lat (float): Latitude of the center point
            lng (float): Longitude of the center point
            radius (float): Approximate radius in degrees (default: 0.05 ≈ 5km)

        Example: /api/buildings/nearby/?lat=19.07&lng=72.87&radius=0.1
        """
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = float(request.query_params.get("radius", 0.05))

        if not lat or not lng:
            return Response(
                {"error": "Both lat and lng query parameters are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lat = float(lat)
        lng = float(lng)

        queryset = Building.objects.filter(
            latitude__gte=lat - radius,
            latitude__lte=lat + radius,
            longitude__gte=lng - radius,
            longitude__lte=lng + radius,
        ).order_by("-avg_rating")[:50]

        serializer = BuildingNearbySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="top-rated")
    def top_rated(self, request):
        """
        Returns the top-rated buildings.

        Query params:
            limit (int): Number of buildings to return (default: 10, max: 50)
            city (str): Optional city filter
        """
        limit = min(int(request.query_params.get("limit", 10)), 50)
        city = request.query_params.get("city")

        queryset = Building.objects.filter(
            avg_rating__isnull=False,
            review_count__gte=1,
        )

        if city:
            queryset = queryset.filter(city__iexact=city)

        queryset = queryset.order_by("-avg_rating", "-review_count")[:limit]
        serializer = BuildingNearbySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def images(self, request, pk=None):
        """Get all images for this building."""
        building = self.get_object()
        images = building.images_set.all()
        serializer = BuildingImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_image(self, request, pk=None):
        """
        Add an image URL to this building.
        POST body: { "image": "https://example.com/photo.jpg" }
        """
        building = self.get_object()
        image_url = request.data.get("image")
        if not image_url:
            return Response(
                {"error": "image URL is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        Images.objects.create(image=image_url, build_ID=building)
        return Response(
            {"message": "Image added successfully"}, status=status.HTTP_201_CREATED
        )


#  BUILDING IMAGE VIEWS (standalone CRUD)


class BuildingImageViewSet(viewsets.ModelViewSet):
    """
    Standalone CRUD for building images.
    For adding images to a specific building, prefer
    /api/buildings/{id}/add_image/ instead.
    """

    queryset = Images.objects.select_related("build_ID").all()
    serializer_class = BuildingImageSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["build_ID"]


# Public views


class PublicBuildingListView(generics.ListAPIView):
    """
    Public-facing building search for tenants.
    Returns RERA-verified buildings only, sorted by rating.
    """

    queryset = Building.objects.filter(is_RERA_verified=True).order_by("-avg_rating")
    serializer_class = BuildingListSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = BuildingFilter
    search_fields = ["name", "address", "city"]
    ordering_fields = ["avg_rating", "review_count", "name"]
    ordering = ["-avg_rating"]


class PublicBuildingDetailView(generics.RetrieveAPIView):
    """Public-facing detail view for a single building."""

    queryset = Building.objects.prefetch_related("images_set").all()
    serializer_class = BuildingSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
