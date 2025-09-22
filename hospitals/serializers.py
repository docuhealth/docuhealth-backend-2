from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import HospitalProfile
from core.models import User, UserProfileImage

class CreateHospitalSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    profile = HospitalProfile(required=True)
    
    street = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['email', 'role', 'street', 'city', 'state','country', 'created_at', 'updated_at', 'profile', 'password', 'house_no']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        role = validated_data.get('role')
        
        house_no = validated_data.pop('house_no', None)
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'

        user = super().create(validated_data) 

        if role == User.Role.PATIENT:
            HospitalProfile.objects.create(user=user, **profile_data)
            
        return user