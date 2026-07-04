from django.db import models
from ..common.models import BaseModel


class Building(BaseModel):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    Pin_code = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    built_year = models.DateField(null=True, blank=True)
    no_of_units = models.IntegerField(null=True, blank=True)
    no_of_floors = models.IntegerField(null=True, blank=True)
    is_gym = models.BooleanField(default=False)
    is_swimming = models.BooleanField(default=False)
    is_garden = models.BooleanField(default=False)
    review_count = models.IntegerField(null=True, blank=True)
    avg_rating = models.FloatField(null=True, blank=True)
    is_elevator = models.BooleanField(default=False)
    is_RERA_verified = models.BooleanField(default=False)
