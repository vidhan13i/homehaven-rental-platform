import django_filters
from django.db.models import Q
from listings.models import Listing, Unit, Agent


# ─── LISTING FILTERS ──────────────────────────────────────────────────────────

class ListingFilter(django_filters.FilterSet):
    """
    Advanced filter for Listings.
    Supports range queries on rent, deposit, lease_term, and dates.
    """

    is_verified = django_filters.BooleanFilter(field_name='is_listing_verified')
    unit = django_filters.UUIDFilter(field_name='unit_ID')

    min_rent = django_filters.NumberFilter(field_name='rent', lookup_expr='gte')
    max_rent = django_filters.NumberFilter(field_name='rent', lookup_expr='lte')

    min_deposit = django_filters.NumberFilter(field_name='deposit_amount', lookup_expr='gte')
    max_deposit = django_filters.NumberFilter(field_name='deposit_amount', lookup_expr='lte')

    min_lease_term = django_filters.NumberFilter(field_name='lease_term', lookup_expr='gte')
    max_lease_term = django_filters.NumberFilter(field_name='lease_term', lookup_expr='lte')

    available_from = django_filters.DateFilter(field_name='available_date', lookup_expr='gte')
    available_to = django_filters.DateFilter(field_name='available_date', lookup_expr='lte')

    published_after = django_filters.DateFilter(field_name='publish_date', lookup_expr='gte')
    published_before = django_filters.DateFilter(field_name='publish_date', lookup_expr='lte')

    # Filter by agent (cross FK: listing → unit → agent)
    agent = django_filters.UUIDFilter(field_name='unit_ID__agent_ID')

    # Filter by furnishing (cross FK: listing → unit)
    is_furnished = django_filters.BooleanFilter(field_name='unit_ID__is_furnished')

    # Filter by bedrooms and bathrooms
    bedrooms = django_filters.NumberFilter(field_name='unit_ID__no_bedrooms', lookup_expr='gte')
    bathrooms = django_filters.NumberFilter(field_name='unit_ID__no_bathrooms', lookup_expr='gte')

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Listing
        fields = {
            'rent': ['exact', 'gte', 'lte'],
            'deposit_amount': ['exact', 'gte', 'lte'],
            'lease_term': ['exact', 'gte', 'lte'],
            'is_listing_verified': ['exact'],
            'available_date': ['exact', 'gte', 'lte'],
        }

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(unit_ID__full_address__icontains=value) |
            Q(unit_ID__description__icontains=value)
        )


class AvailableListingFilter(ListingFilter):
    """
    Extends ListingFilter but restricts to currently-available listings.
    Used by the public-facing endpoint.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        self.queryset = self.queryset.filter(
            available_date__gte=timezone.now().date()
        )


# ─── UNIT FILTERS ─────────────────────────────────────────────────────────────

class UnitFilter(django_filters.FilterSet):
    """
    Advanced filter for Units.
    Supports filtering by furnishing, bedrooms, bathrooms, and agent.
    """

    agent = django_filters.UUIDFilter(field_name='agent_ID')

    min_bedrooms = django_filters.NumberFilter(field_name='no_bedrooms', lookup_expr='gte')
    max_bedrooms = django_filters.NumberFilter(field_name='no_bedrooms', lookup_expr='lte')

    min_bathrooms = django_filters.NumberFilter(field_name='no_bathrooms', lookup_expr='gte')
    max_bathrooms = django_filters.NumberFilter(field_name='no_bathrooms', lookup_expr='lte')

    is_furnished = django_filters.BooleanFilter(field_name='is_furnished')
    is_semi_furnished = django_filters.BooleanFilter(field_name='is_semi_furnished')

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Unit
        fields = {
            'no_bedrooms': ['exact', 'gte', 'lte'],
            'no_bathrooms': ['exact', 'gte', 'lte'],
            'is_furnished': ['exact'],
            'is_semi_furnished': ['exact'],
        }

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(full_address__icontains=value) |
            Q(unit_no__icontains=value) |
            Q(description__icontains=value)
        )


# ─── AGENT FILTERS ────────────────────────────────────────────────────────────

class AgentFilter(django_filters.FilterSet):
    """
    Advanced filter for Agents.
    Supports filtering by verification status, experience, and organization.
    """

    is_verified = django_filters.BooleanFilter(field_name='is_agent_verified')
    organization = django_filters.CharFilter(field_name='agent_organization', lookup_expr='icontains')

    min_experience = django_filters.NumberFilter(field_name='agent_experience', lookup_expr='gte')
    max_experience = django_filters.NumberFilter(field_name='agent_experience', lookup_expr='lte')

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Agent
        fields = {
            'is_agent_verified': ['exact'],
            'agent_experience': ['exact', 'gte', 'lte'],
        }

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(agent_organization__icontains=value)
        )