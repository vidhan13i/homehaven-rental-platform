from django.db import models
from ..common.models import BaseModel


class Profile(BaseModel):
    userID = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    DOB = models.DateField()
    phone_number = models.IntegerField(null=True, blank=True)

    class GenderChoices(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"
        PREFER_NOT = "P", "Prefer not to say"

    gender = models.CharField(
        max_length=1,
        choices=GenderChoices.choices,
    )

    ethnicity = models.CharField(max_length=200, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
