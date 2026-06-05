from django.db import models
from django.core.exceptions import ValidationError

from ..common.models import BaseModel

def required_documents(value):
    required_keys = {"employment_letter", "aadhar_card", "pan_card","ITR","bank_statement"}

    if not isinstance(value, dict):
        raise ValidationError("required_documents must be a JSON object")

    if not required_keys.issubset(value.keys()):
        raise ValidationError(
            "required_documents must contain employment_letter, aadhar_card, pan_card, ITR, bank_statement"
        )

class Document(BaseModel):
    label = models.JSONField(
        validators=[required_documents],
        null=True,
        blank=True,
    )
    file_field = models.FileField(
        upload_to="documents/",
        null=True,
        blank=True,
    )
    applicant_ID = models.ForeignKey(
        "Applicant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="document",
    )