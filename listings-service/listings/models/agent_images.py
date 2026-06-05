from django.db import models


from ..common.models import BaseModel

class AgentImages(BaseModel):
    agent_ID = models.ForeignKey(
        "Agent",
        on_delete=models.CASCADE,
    )
    agent_image_url = models.URLField(max_length=200)