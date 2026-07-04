from django.db import models
from django.core.exceptions import ValidationError

from ..common.models import BaseModel
import uuid


def resident_info(value):
    required_keys = {"name", "gender", "dob"}

    if not isinstance(value, dict):
        raise ValidationError("resident_info must be a JSON object")

    if not required_keys.issubset(value.keys()):
        raise ValidationError("resident_info must contain name, gender, and dob")

    if value["gender"] not in {"male", "female", "other"}:
        raise ValidationError("gender must be male, female, or other")


class Application(BaseModel):
    unit_ID = models.UUIDField(default=uuid.uuid4, editable=False)
    building_ID = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=["unit_ID"]),
            models.Index(fields=["building_ID"]),
        ]

    applicant_ID = models.ForeignKey(
        "Applicant", on_delete=models.CASCADE, related_name="application"
    )
    submitted_at_date = models.DateField(auto_now_add=True)
    lease_term = models.CharField(max_length=200)
    resident_info = models.JSONField(validators=[resident_info])

    class ApplicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
    )
