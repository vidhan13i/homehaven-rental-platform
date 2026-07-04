from django.db import models
from ..common.models import BaseModel


class Images(BaseModel):
    image = models.URLField()
    build_ID = models.ForeignKey(
        "Building",
        on_delete=models.CASCADE,
    )
