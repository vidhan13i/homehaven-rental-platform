from django.db import models


from ..common.models import BaseModel


class Images(BaseModel):
    image_url = models.CharField(max_length=200)
    unit_ID = models.ForeignKey(
        "Unit",
        on_delete=models.CASCADE,
        related_name="images",
    )
