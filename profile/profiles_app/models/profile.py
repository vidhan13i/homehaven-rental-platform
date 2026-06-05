from django.db import models
from ..common.models import BaseModel



class Profile(BaseModel):
    userID = models.CharField(max_length=100),
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    DOB = models.DateField()
    phone_number = models.IntegerField(null=True, blank=True)

    class User_Gender(models.Model):
        GENDER_CHOICES = [
            ('M', 'Male'),
            ('F', 'Female'),
            ('O', 'Other'),
            ('P', 'Prefer not to say'),
        ]

    gender = models.CharField(
        max_length=1,
        choices=User_Gender.GENDER_CHOICES,
        )
    ethnicity = models.CharField(max_length=200),
    is_email_verified = models.BooleanField(default=False)