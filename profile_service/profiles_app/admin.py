from django.contrib import admin
from profiles_app.models import Profile, EmailOTP


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "gender",
        "is_email_verified",
        "created_at",
    ]
    list_filter = ["is_email_verified", "gender"]
    search_fields = ["first_name", "last_name", "email", "userID"]
    list_editable = ["is_email_verified"]


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ["email", "expiry_date", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["email"]
