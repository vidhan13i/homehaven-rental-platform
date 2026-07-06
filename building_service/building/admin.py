from django.contrib import admin
from building.models import Building, Images




class BuildingImageInline(admin.TabularInline):
    """Show building images directly inside the Building admin page."""

    model = Images
    extra = 1
    fields = ["image", "created_at"]
    readonly_fields = ["created_at"]





@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "city",
        "state",
        "Pin_code",
        "no_of_floors",
        "no_of_units",
        "avg_rating",
        "review_count",
        "is_RERA_verified",
        "created_at",
    ]
    list_filter = [
        "is_RERA_verified",
        "is_gym",
        "is_swimming",
        "is_garden",
        "is_elevator",
        "city",
        "state",
    ]
    search_fields = ["name", "address", "city", "state", "slug"]
    list_editable = ["is_RERA_verified"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BuildingImageInline]
    fieldsets = (
        (
            "Basic Info",
            {"fields": ("name", "address", "slug", "city", "state", "Pin_code")},
        ),
        (
            "Location",
            {
                "fields": ("latitude", "longitude"),
                "classes": ("collapse",),
            },
        ),
        ("Building Details", {"fields": ("built_year", "no_of_units", "no_of_floors")}),
        (
            "Amenities",
            {"fields": ("is_gym", "is_swimming", "is_garden", "is_elevator")},
        ),
        (
            "Reviews & Verification",
            {"fields": ("review_count", "avg_rating", "is_RERA_verified")},
        ),
    )


@admin.register(Images)
class BuildingImagesAdmin(admin.ModelAdmin):
    list_display = ["id", "image", "build_ID", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["image"]
