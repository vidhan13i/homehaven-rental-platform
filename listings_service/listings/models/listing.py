from django.db import models

from ..common.models import BaseModel


class Listing(BaseModel):
    rent = models.IntegerField(null=True, blank=True)
    deposit_amount = models.IntegerField(null=True, blank=True)
    available_date = models.DateField(null=True, blank=True)
    publish_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    lease_term = models.IntegerField(null=True, blank=True)
    is_listing_verified = models.BooleanField(default=False)
    unit_ID = models.ForeignKey(
        "Unit",
        on_delete=models.CASCADE,
        related_name="Listings",
    )
