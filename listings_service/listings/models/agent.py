from django.db import models
from ..common.models import BaseModel

class Agent(BaseModel):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.IntegerField(null=True, blank=True)
    agent_organization= models.CharField(max_length=200)
    agent_experience = models.IntegerField(null=True, blank=True)
    is_agent_verified = models.BooleanField(default=False)

