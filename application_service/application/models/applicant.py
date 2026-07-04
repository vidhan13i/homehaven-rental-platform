import datetime
import uuid

from django.db import models
from django.core.exceptions import ValidationError

from ..common.models import BaseModel


def rental_history(value):
    required_keys = {"address", "move_in", "move_out"}

    if not isinstance(value, dict):
        raise ValidationError("resident_info must be a JSON object")

    if not required_keys.issubset(value.keys()):
        raise ValidationError(
            "rental_history must contain address, move_in, and move_out"
        )

    if not isinstance(value["address"], str):
        raise ValidationError("address must be a string")

    try:
        move_in = datetime.strptime(value["move_in"], "%Y-%m-%d").date()
        move_out = datetime.strptime(value["move_out"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValidationError("move_in and move_out must be dates in YYYY-MM-DD format")

    if move_out < move_in:
        raise ValidationError("move_out date cannot be earlier than move_in date")


def emergency_info(value):
    required_keys = {"name", "email", "phone", "relationship"}
    if not isinstance(value, dict):
        raise ValidationError("emergency_info must be a JSON object")
    if not required_keys.issubset(value.keys()):
        raise ValidationError(
            "emergency_info must contain name, email, phone and relationship"
        )


class Applicant(BaseModel):
    profile_ID = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["profile_ID"]),
        ]

    employer = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    job_start_date = models.DateField(null=True, blank=True)
    credit_score = models.IntegerField(null=True, blank=True)
    income = models.FloatField(null=True, blank=True)
    savings = models.FloatField(null=True, blank=True)
    expected_movein_date = models.DateField(null=True)
    reason = models.TextField(null=True, blank=True)
    has_rented_before = models.BooleanField(default=False)
    rental_history = models.JSONField(
        validators=[rental_history],
        null=True,
        blank=True,
    )

    marital_status = models.BooleanField(default=False)
    children = models.BooleanField(default=False)
    emergency_info = models.JSONField(
        validators=[emergency_info],
    )
