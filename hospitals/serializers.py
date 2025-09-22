from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import HospitalProfile
from core.models import User, UserProfileImage
from core.serializers import BaseUserCreateSerializer

class HospitalProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= HospitalProfile
        fields = ['firstname', 'lastname']
        read_only_fields = ['hin']

class CreateHospitalSerializer(BaseUserCreateSerializer):
    profile = HospitalProfileSerializer(required=True, source="hospital_profile")
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "house_no"]

    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_profile")
        
        validated_data['role'] = User.Role.HOSPITAL
        
        user = super().create_user(validated_data)
        HospitalProfile.objects.create(user=user, **profile_data)
        
        return user