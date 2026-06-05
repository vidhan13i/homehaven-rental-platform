import django_filters
from django.db.models import Q
from building.building.models import Building

class BuildingFilter(django_filters.FilterSet):
    class Meta:
        model = Building
