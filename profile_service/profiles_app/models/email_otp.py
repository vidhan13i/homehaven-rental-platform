from django.db import models
from ..common.models import BaseModel

class EmailOTP(BaseModel):
    email = models.EmailField()
    otp_hash = models.CharField()
    expiry_date = models.DateTimeField()
