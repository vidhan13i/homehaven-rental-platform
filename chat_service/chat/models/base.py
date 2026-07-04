"""
Base model for all chat service models.

Mirrors the BaseModel pattern used in:
  - application_service/application/common/models.py
  - listings_service/listings/common/models.py

Every model in the chat service inherits from ChatBaseModel.
"""

import uuid
from django.db import models


class ChatBaseModel(models.Model):
    """Abstract base with UUID primary key and audit timestamps."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
