from django.contrib import admin
from listings.models import Listing, Unit, Agent, Images, AgentImages


# ─── INLINE MODELS (show child records inside parent's admin page) ────────────

class UnitImageInline(admin.TabularInline):
    """Show unit images directly inside the Unit admin page."""
    model = Images
    extra = 1  # Show 1 empty row for adding new images


class ListingInline(admin.TabularInline):
    """Show listings directly inside the Unit admin page."""
    model = Listing
    extra = 0
    fields = ['rent', 'deposit_amount', 'available_date', 'is_listing_verified']
    readonly_fields = ['created_at']


class UnitInline(admin.TabularInline):
    """Show units directly inside the Agent admin page."""
    model = Unit
    extra = 0
    fields = ['unit_no', 'full_address', 'no_bedrooms', 'is_furnished']
    readonly_fields = ['created_at']


class AgentImageInline(admin.TabularInline):
    """Show agent images directly inside the Agent admin page."""
    model = AgentImages
    extra = 1


# ─── MODEL ADMIN CLASSES ─────────────────────────────────────────────────────

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'first_name', 'last_name', 'email',
        'agent_organization', 'agent_experience', 'is_agent_verified',
    ]
    list_filter = ['is_agent_verified', 'agent_organization']
    search_fields = ['first_name', 'last_name', 'email', 'agent_organization']
    list_editable = ['is_agent_verified']
    inlines = [UnitInline, AgentImageInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'unit_no', 'full_address', 'no_bedrooms',
        'no_bathrooms', 'is_furnished', 'is_semi_furnished', 'agent_ID',
    ]
    list_filter = ['is_furnished', 'is_semi_furnished', 'no_bedrooms']
    search_fields = ['full_address', 'unit_no', 'description']
    inlines = [UnitImageInline, ListingInline]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'rent', 'deposit_amount', 'available_date',
        'lease_term', 'is_listing_verified', 'unit_ID', 'created_at',
    ]
    list_filter = ['is_listing_verified', 'available_date']
    search_fields = ['unit_ID__full_address', 'rent']
    list_editable = ['is_listing_verified']
    date_hierarchy = 'available_date'


@admin.register(Images)
class ImagesAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_url', 'unit_ID', 'created_at']
    list_filter = ['created_at']
    search_fields = ['image_url']


@admin.register(AgentImages)
class AgentImagesAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent_image_url', 'agent_ID', 'created_at']
    list_filter = ['created_at']
    search_fields = ['agent_image_url']
