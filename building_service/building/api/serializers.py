from rest_framework import serializers
from building.models import Building, Images


# ─── BUILDING IMAGE SERIALIZERS ───────────────────────────────────────────────

class BuildingImageSerializer(serializers.ModelSerializer):
    """Serializer for building photos."""

    class Meta:
        model = Images
        fields = ['id', 'image', 'build_ID', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─── BUILDING SERIALIZERS ─────────────────────────────────────────────────────

class BuildingSerializer(serializers.ModelSerializer):
    """
    Full Building detail serializer.
    Includes nested images and computed amenities summary.
    """
    images = BuildingImageSerializer(source='images_set', many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            'id', 'name', 'address', 'slug', 'city', 'state', 'Pin_code',
            'latitude', 'longitude', 'built_year',
            'no_of_units', 'no_of_floors',
            'is_gym', 'is_swimming', 'is_garden', 'is_elevator',
            'is_RERA_verified',
            'review_count', 'avg_rating',
            'amenities', 'images', 'image_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_image_count(self, obj):
        return obj.images_set.count()

    def get_amenities(self, obj):
        """Returns a list of available amenities for easy frontend display."""
        amenities = []
        if obj.is_gym:
            amenities.append('Gym')
        if obj.is_swimming:
            amenities.append('Swimming Pool')
        if obj.is_garden:
            amenities.append('Garden')
        if obj.is_elevator:
            amenities.append('Elevator')
        return amenities


class BuildingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for search results / map markers.
    Only includes essential fields to keep the payload small.
    """
    amenities = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            'id', 'name', 'slug', 'city', 'state',
            'latitude', 'longitude',
            'no_of_units', 'no_of_floors',
            'avg_rating', 'review_count',
            'is_RERA_verified', 'amenities',
        ]

    def get_amenities(self, obj):
        amenities = []
        if obj.is_gym:
            amenities.append('Gym')
        if obj.is_swimming:
            amenities.append('Swimming Pool')
        if obj.is_garden:
            amenities.append('Garden')
        if obj.is_elevator:
            amenities.append('Elevator')
        return amenities


class BuildingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating buildings with validation."""

    class Meta:
        model = Building
        fields = [
            'name', 'address', 'slug', 'city', 'state', 'Pin_code',
            'latitude', 'longitude', 'built_year',
            'no_of_units', 'no_of_floors',
            'is_gym', 'is_swimming', 'is_garden', 'is_elevator',
            'is_RERA_verified',
            'review_count', 'avg_rating',
        ]

    def validate_Pin_code(self, value):
        if value is not None and (value < 100000 or value > 999999):
            raise serializers.ValidationError("Pin code must be a 6-digit number")
        return value

    def validate_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value

    def validate_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value

    def validate_no_of_floors(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Number of floors must be positive")
        return value

    def validate_no_of_units(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Number of units must be positive")
        return value

    def validate_avg_rating(self, value):
        if value is not None and (value < 0 or value > 5):
            raise serializers.ValidationError("Rating must be between 0 and 5")
        return value


class BuildingNearbySerializer(serializers.ModelSerializer):
    """
    Minimal serializer for map/nearby queries.
    Only lat, lng, name, and rating — used for map pin rendering.
    """

    class Meta:
        model = Building
        fields = ['id', 'name', 'slug', 'latitude', 'longitude', 'avg_rating', 'review_count']
