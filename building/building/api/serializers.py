from rest_framework import serializers
from building.building.models.building import Building

class BuildingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Building
        fields = '__all__'

        read_only_fields = ('id','created_at','updated_at')

class BuildingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'
        read_only_fields = ('id','created_at','updated_at')

class BuildingCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['name','address','slug','city','state','Pin_code','latitude','longitude','built_year','no_of_units','no_of_floors','is_gym','is_swimming','is_garden','review_count','avg_rating','is_elevator','is_RERA_verified']
        read_only_fields = ('id','created_at','updated_at')



