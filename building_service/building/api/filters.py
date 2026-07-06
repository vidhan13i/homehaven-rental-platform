import django_filters
from django.db.models import Q
from building.models import Building


class BuildingFilter(django_filters.FilterSet):
    """
    Advanced filter for Buildings.
    Supports city/state search, amenity filtering, rating ranges,
    and geographic bounding-box queries for map views.
    """

    # ── Location filters ──
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    state = django_filters.CharFilter(field_name="state", lookup_expr="iexact")
    pin_code = django_filters.NumberFilter(field_name="Pin_code")

    # ── Amenity filters (boolean) ──
    has_gym = django_filters.BooleanFilter(field_name="is_gym")
    has_swimming = django_filters.BooleanFilter(field_name="is_swimming")
    has_garden = django_filters.BooleanFilter(field_name="is_garden")
    has_elevator = django_filters.BooleanFilter(field_name="is_elevator")
    is_rera_verified = django_filters.BooleanFilter(field_name="is_RERA_verified")

    # ── Size filters ──
    min_floors = django_filters.NumberFilter(
        field_name="no_of_floors", lookup_expr="gte"
    )
    max_floors = django_filters.NumberFilter(
        field_name="no_of_floors", lookup_expr="lte"
    )
    min_units = django_filters.NumberFilter(field_name="no_of_units", lookup_expr="gte")
    max_units = django_filters.NumberFilter(field_name="no_of_units", lookup_expr="lte")

    # ── Rating filters ──
    min_rating = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="lte")
    min_reviews = django_filters.NumberFilter(
        field_name="review_count", lookup_expr="gte"
    )


    lat_min = django_filters.NumberFilter(field_name="latitude", lookup_expr="gte")
    lat_max = django_filters.NumberFilter(field_name="latitude", lookup_expr="lte")
    lng_min = django_filters.NumberFilter(field_name="longitude", lookup_expr="gte")
    lng_max = django_filters.NumberFilter(field_name="longitude", lookup_expr="lte")

    # ── Built year ──
    built_after = django_filters.NumberFilter(
        field_name="built_year", lookup_expr="gte"
    )
    built_before = django_filters.NumberFilter(
        field_name="built_year", lookup_expr="lte"
    )

    # ── Full-text search ──
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Building
        fields = {
            "city": ["exact", "iexact"],
            "state": ["exact", "iexact"],
            "is_RERA_verified": ["exact"],
            "avg_rating": ["gte", "lte"],
            "no_of_floors": ["gte", "lte"],
        }

    def filter_search(self, queryset, name, value):
        """Search across name, address, city, and state."""
        return queryset.filter(
            Q(name__icontains=value)
            | Q(address__icontains=value)
            | Q(city__icontains=value)
            | Q(state__icontains=value)
        )
