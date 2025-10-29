from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import HospitalProfile, DoctorProfile, HospitalInquiry, HospitalVerificationRequest
from core.models import User, UserProfileImage
from core.serializers import BaseUserCreateSerializer

class HospitalProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model= HospitalProfile
        fields = ['firstname', 'lastname', 'hin']
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
    
class DoctorProfileSerializer(serializers.ModelSerializer):
    hospital = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=True)
    class Meta:
        model= DoctorProfile
        fields = ['specialization', 'license_no', 'hospital', 'firstname', 'lastname', 'doc_id']
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
    
class HospitalInquirySerializer(serializers.ModelSerializer):
    redirect_url = serializers.URLField(required=True, allow_blank=True, write_only=True)
    
    class Meta:
        model= HospitalInquiry
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['status', 'created_at', 'updated_at']
        
class HospitalVerificationRequestSerializer(serializers.ModelSerializer):
    inquiry = serializers.PrimaryKeyRelatedField(queryset=HospitalInquiry.objects.all())
    documents = serializers.ListField(child=serializers.DictField())
    
    class Meta:
        model= HospitalVerificationRequest
        exclude = ['is_deleted', 'deleted_at' ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'reviewed_by']
        
class ApproveVerificationRequestSerializer(serializers.Serializer):
    verification_request = serializers.PrimaryKeyRelatedField(queryset=HospitalVerificationRequest.objects.all())
    redirect_url = serializers.URLField(required=True, allow_blank=True)