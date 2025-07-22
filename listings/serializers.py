from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import Property

class PropertySerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True, required=True)
    longitude = serializers.FloatField(write_only=True, required=True)
    coordinates = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'street_address', 'suburb', 'city', 'state_or_region', 'country',
            'latitude', 'longitude', 'coordinates',
            # add other fields as needed
        ]

    def get_coordinates(self, obj):
        if obj.location:
            return {'latitude': obj.location.y, 'longitude': obj.location.x}
        return None

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lng = validated_data.pop('longitude')
        validated_data['location'] = Point(lng, lat)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat)
        return super().update(instance, validated_data)