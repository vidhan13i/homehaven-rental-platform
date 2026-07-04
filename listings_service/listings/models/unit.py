from django.db import models
from django.db.models import Q

from ..common.models import BaseModel


class Unit(BaseModel):
    full_address = models.CharField(max_length=200)
    unit_no = models.CharField(max_length=40)
    unit_slug = models.SlugField(max_length=200)
    no_bedrooms = models.IntegerField(null=True, blank=True)
    no_bathrooms = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_furnished = models.BooleanField(default=False)
    is_semi_furnished = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~(Q(is_furnished=True) & Q(is_semi_furnished=True)),
                name="TT not allowed",
            )
        ]

    agent_ID = models.ForeignKey(
        "Agent",
        on_delete=models.CASCADE,
        related_name="units",
    )
