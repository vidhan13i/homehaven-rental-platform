import django_filters
from django.db.models import Q
from listings.listings.models import Listing


class ListingFilter(django_filters.FilterSet):


    is_verified = django_filters.BooleanFilter(field_name='is_listing_verified')
    unit = django_filters.NumberFilter(field_name='unit_ID')

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
            Q(unit_ID__address__icontains=value) |
            Q(rent__icontains=value)
        )


class AvailableListingFilter(ListingFilter):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone

        self.queryset = self.queryset.filter(
            available_date__gte=timezone.now().date()
        )