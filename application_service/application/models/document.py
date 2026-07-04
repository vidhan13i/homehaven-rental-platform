from django.db import models

from ..common.models import BaseModel

class Document(BaseModel):
    label = models.CharField(
        max_length=255,
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