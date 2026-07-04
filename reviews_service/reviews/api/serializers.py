from rest_framework import serializers
from reviews.models.reviews import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Full review detail with computed average rating."""

    avg_rating = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    rent_change = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "profile_ID",
            "building_ID",
            "full_address",
            "unit_no",
            "Title",
            "Pros",
            "Cons",
            "Advice",
            "cleanliness_rating",
            "garbage_management_rating",
            "neighbours_rating",
            "water_supply_rating",
            "building_maintenance_rating",
            "avg_rating",
            "move_in_date",
            "move_out_date",
            "is_received_deposit",
            "total_deposit",
            "deposit_withheld",
            "is_pet_friendly",
            "starting_rent",
            "ending_rent",
            "rent_change",
            "status",
            "status_display",
            "review_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "review_date", "created_at", "updated_at"]

    def get_avg_rating(self, obj):
        ratings = [
            obj.cleanliness_rating,
            obj.garbage_management_rating,
            obj.neighbours_rating,
            obj.water_supply_rating,
            obj.building_maintenance_rating,
        ]
        return round(sum(ratings) / len(ratings), 2)

    def get_rent_change(self, obj):
        if obj.starting_rent and obj.ending_rent:
            change = obj.ending_rent - obj.starting_rent
            pct = (change / obj.starting_rent) * 100 if obj.starting_rent > 0 else 0
            return {"amount": change, "percentage": round(pct, 1)}
        return None


class ReviewListSerializer(serializers.ModelSerializer):
    """Lightweight review for list/search views."""

    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "building_ID",
            "Title",
            "avg_rating",
            "is_pet_friendly",
            "status",
            "review_date",
        ]

    def get_avg_rating(self, obj):
        ratings = [
            obj.cleanliness_rating,
            obj.garbage_management_rating,
            obj.neighbours_rating,
            obj.water_supply_rating,
            obj.building_maintenance_rating,
        ]
        return round(sum(ratings) / len(ratings), 2)


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating reviews with validation."""

    class Meta:
        model = Review
        fields = [
            "profile_ID",
            "building_ID",
            "full_address",
            "unit_no",
            "Title",
            "Pros",
            "Cons",
            "Advice",
            "cleanliness_rating",
            "garbage_management_rating",
            "neighbours_rating",
            "water_supply_rating",
            "building_maintenance_rating",
            "move_in_date",
            "move_out_date",
            "is_received_deposit",
            "total_deposit",
            "deposit_withheld",
            "is_pet_friendly",
            "starting_rent",
            "ending_rent",
            "status",
        ]

    def validate(self, data):
        if data.get("move_in_date") and data.get("move_out_date"):
            if data["move_out_date"] < data["move_in_date"]:
                raise serializers.ValidationError(
                    "Move-out date cannot be before move-in date"
                )

        if data.get("deposit_withheld") and data.get("total_deposit"):
            if data["deposit_withheld"] > data["total_deposit"]:
                raise serializers.ValidationError(
                    "Deposit withheld cannot exceed total deposit"
                )

        # Validate all ratings are 0-5
        rating_fields = [
            "cleanliness_rating",
            "garbage_management_rating",
            "neighbours_rating",
            "water_supply_rating",
            "building_maintenance_rating",
        ]
        for field in rating_fields:
            value = data.get(field)
            if value is not None and (value < 0 or value > 5):
                raise serializers.ValidationError(f"{field} must be between 0 and 5")

        return data
