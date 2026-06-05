from rest_framework import serializers
from listings.models import Listing
from listings.models.unit import Unit


class UnitSerializer(serializers.ModelSerializer):


    class Meta:
        model = Unit
        fields = '__all__'


class ListingSerializer(serializers.ModelSerializer):

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
    unit_address = serializers.CharField(source='unit_ID.address', read_only=True)

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
