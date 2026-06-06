from rest_framework import serializers
from listings.models import Listing, Unit, Agent, Images, AgentImages


# ─── AGENT SERIALIZERS ────────────────────────────────────────────────────────

class AgentImageSerializer(serializers.ModelSerializer):
    """Serializer for agent profile photos / documents."""

    class Meta:
        model = AgentImages
        fields = ['id', 'agent_image_url', 'agent_ID', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentSerializer(serializers.ModelSerializer):
    """
    Full Agent detail serializer.
    Includes nested images and a computed 'full_name' field.
    """
    images = AgentImageSerializer(source='agentimages_set', many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    unit_count = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email',
            'phone_number', 'agent_organization', 'agent_experience',
            'is_agent_verified', 'images', 'unit_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_unit_count(self, obj):
        return obj.units.count()


class AgentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing agents in a table/list view."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Agent
        fields = [
            'id', 'full_name', 'email', 'phone_number',
            'agent_organization', 'is_agent_verified',
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AgentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating agents with validation."""

    class Meta:
        model = Agent
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'agent_organization', 'agent_experience', 'is_agent_verified',
        ]

    def validate_agent_experience(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Experience cannot be negative")
        return value

    def validate_phone_number(self, value):
        if value is not None and len(str(value)) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value


# ─── UNIT SERIALIZERS ─────────────────────────────────────────────────────────

class UnitImageSerializer(serializers.ModelSerializer):
    """Serializer for unit photos."""

    class Meta:
        model = Images
        fields = ['id', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UnitSerializer(serializers.ModelSerializer):
    """
    Full Unit detail serializer.
    Includes nested images, agent name, and active listing count.
    """
    images = UnitImageSerializer(many=True, read_only=True)
    agent_name = serializers.SerializerMethodField()
    listing_count = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            'id', 'full_address', 'unit_no', 'unit_slug',
            'no_bedrooms', 'no_bathrooms', 'description',
            'is_furnished', 'is_semi_furnished',
            'agent_ID', 'agent_name', 'images', 'listing_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_agent_name(self, obj):
        return f"{obj.agent_ID.first_name} {obj.agent_ID.last_name}"

    def get_listing_count(self, obj):
        return obj.Listings.count()


class UnitListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing units in a table/list view."""
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            'id', 'full_address', 'unit_no', 'no_bedrooms',
            'no_bathrooms', 'is_furnished', 'is_semi_furnished',
            'agent_ID', 'agent_name',
        ]

    def get_agent_name(self, obj):
        return f"{obj.agent_ID.first_name} {obj.agent_ID.last_name}"


class UnitCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating units with validation.
    Enforces the constraint that a unit cannot be BOTH furnished and semi-furnished.
    """

    class Meta:
        model = Unit
        fields = [
            'full_address', 'unit_no', 'unit_slug',
            'no_bedrooms', 'no_bathrooms', 'description',
            'is_furnished', 'is_semi_furnished', 'agent_ID',
        ]

    def validate(self, data):
        # Enforce the same constraint that exists at DB level
        if data.get('is_furnished') and data.get('is_semi_furnished'):
            raise serializers.ValidationError(
                "A unit cannot be both furnished and semi-furnished."
            )

        if data.get('no_bedrooms') is not None and data['no_bedrooms'] < 0:
            raise serializers.ValidationError("Number of bedrooms cannot be negative")

        if data.get('no_bathrooms') is not None and data['no_bathrooms'] < 0:
            raise serializers.ValidationError("Number of bathrooms cannot be negative")

        return data


# ─── LISTING SERIALIZERS ──────────────────────────────────────────────────────

class ListingSerializer(serializers.ModelSerializer):
    """
    Full Listing detail serializer.
    Embeds the full Unit details (including images and agent) so the
    frontend gets everything in one API call.
    """
    unit_details = UnitSerializer(source='unit_ID', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'rent',
            'deposit_amount',
            'available_date',
            'publish_date',
            'closing_date',
            'lease_term',
            'is_listing_verified',
            'unit_ID',
            'unit_details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ListingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing page / search results."""
    unit_address = serializers.CharField(source='unit_ID.full_address', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id',
            'rent',
            'deposit_amount',
            'available_date',
            'is_listing_verified',
            'unit_ID',
            'unit_address',
        ]


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating listings with business logic validation."""

    class Meta:
        model = Listing
        fields = [
            'rent',
            'deposit_amount',
            'available_date',
            'publish_date',
            'closing_date',
            'lease_term',
            'is_listing_verified',
            'unit_ID',
        ]

    def validate_rent(self, value):
        if value <= 0:
            raise serializers.ValidationError("Rent must be greater than 0")
        return value

    def validate_deposit_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Deposit amount cannot be negative")
        return value

    def validate(self, data):
        if data.get('available_date') and data.get('closing_date'):
            if data['available_date'] > data['closing_date']:
                raise serializers.ValidationError(
                    "Available date cannot be after closing date"
                )
        return data
