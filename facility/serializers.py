from rest_framework import serializers

from .models import HospitalWard, WardBed

class WardBedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WardBed  
        fields = ['bed_number', 'status', 'id']   
        read_only_fields = ['id']
    
class WardSerializer(serializers.ModelSerializer):
    beds = WardBedSerializer(many=True, read_only=True)
    available_beds = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = HospitalWard
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['available_beds', 'id', 'hospital']
        
class WardBasicInfoSerializer(serializers.ModelSerializer):
    available_beds = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = HospitalWard
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['available_beds', 'id', 'hospital']
        
class WardNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalWard
        fields = ['id', 'name']
        read_only_fields = fields