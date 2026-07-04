from django.contrib import admin
from reviews.models.reviews import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "Title",
        "building_ID",
        "profile_ID",
        "cleanliness_rating",
        "water_supply_rating",
        "status",
        "is_pet_friendly",
        "is_received_deposit",
        "review_date",
    ]
    list_filter = ["status", "is_pet_friendly", "is_received_deposit"]
    search_fields = ["Title", "Pros", "Cons", "full_address"]
    list_editable = ["status"]
    date_hierarchy = "move_in_date"
    fieldsets = (
        (
            "Review Info",
            {
                "fields": (
                    "profile_ID",
                    "building_ID",
                    "full_address",
                    "unit_no",
                    "status",
                )
            },
        ),
        ("Content", {"fields": ("Title", "Pros", "Cons", "Advice")}),
        (
            "Ratings",
            {
                "fields": (
                    "cleanliness_rating",
                    "garbage_management_rating",
                    "neighbours_rating",
                    "water_supply_rating",
                    "building_maintenance_rating",
                )
            },
        ),
        (
            "Tenancy Details",
            {
                "fields": (
                    "move_in_date",
                    "move_out_date",
                    "starting_rent",
                    "ending_rent",
                    "is_pet_friendly",
                )
            },
        ),
        (
            "Deposit Info",
            {
                "fields": ("is_received_deposit", "total_deposit", "deposit_withheld"),
                "classes": ("collapse",),
            },
        ),
    )
