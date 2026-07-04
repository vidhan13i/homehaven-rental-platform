import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from ..common.models import BaseModel


class Review(BaseModel):
    profile_ID = models.UUIDField(default=uuid.uuid4, editable=False)
    building_ID = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["profile_ID"]),
            models.Index(fields=["building_ID"]),
        ]

    full_address = models.TextField(max_length=500)
    review_date = models.DateTimeField(auto_now=True)
    cleanliness_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    garbage_management_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    neighbours_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    water_supply_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    building_maintenance_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    Title = models.TextField(max_length=500)
    Pros = models.TextField(max_length=500)
    Cons = models.TextField(max_length=500)
    Advice = models.TextField(max_length=500)
    move_in_date = models.DateField()
    move_out_date = models.DateField()
    is_received_deposit = models.BooleanField(default=False)
    total_deposit = models.FloatField(null=True, blank=True)
    deposit_withheld = models.FloatField(null=True, blank=True)
    is_pet_friendly = models.BooleanField(default=False)
    starting_rent = models.FloatField(null=True, blank=True)
    ending_rent = models.FloatField(null=True, blank=True)
    unit_no = models.CharField(max_length=200, null=True, blank=True)

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        INPROGRESS = "INPROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
