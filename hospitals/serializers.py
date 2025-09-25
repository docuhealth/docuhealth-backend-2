from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import HospitalProfile, DoctorProfile
from core.models import User, UserProfileImage
from core.serializers import BaseUserCreateSerializer

class HospitalProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= HospitalProfile
        fields = ['firstname', 'lastname']
        read_only_fields = ['doc_id']
        
class CreateHospitalSerializer(BaseUserCreateSerializer):
    profile = HospitalProfileSerializer(required=True, source="hospital_profile")
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "house_no", "hin"]

    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_profile")
        
        validated_data['role'] = User.Role.HOSPITAL
        
        user = super().create_user(validated_data)
        HospitalProfile.objects.create(user=user, **profile_data)
        
        return user
    
class DoctorProfileSerializer(serializers.ModelSerializer):
    hospital = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=True)
    class Meta:
        model= DoctorProfile
        fields = ['specialization', 'license_no', 'hospital', 'doc_id']
        read_only_fields = ['doc_id']
    
class CreateDoctorSerializer(BaseUserCreateSerializer):
    profile = DoctorProfileSerializer(required=True, source="doctor_profile")
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "house_no"]

    def create(self, validated_data):
        profile_data = validated_data.pop("doctor_profile")
        
        validated_data['role'] = User.Role.DOCTOR
        
        user = super().create_user(validated_data)
        DoctorProfile.objects.create(user=user, **profile_data)
        
        return user