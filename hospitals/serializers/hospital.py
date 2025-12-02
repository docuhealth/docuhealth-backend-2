from django.core.exceptions import ValidationError
from rest_framework import serializers

from hospitals.models import HospitalProfile, HospitalInquiry, HospitalVerificationRequest, VerificationToken

from core.models import User
from core.serializers import BaseUserCreateSerializer

class HospitalProfileSerializer(serializers.ModelSerializer):
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    class Meta:
        model= HospitalProfile
        fields = ['name', 'hin', 'street', 'city', 'state', 'country', 'house_no']
        read_only_fields = ['hin']
        
        
class CreateHospitalSerializer(BaseUserCreateSerializer):
    profile = HospitalProfileSerializer(required=True, source="hospital_profile")
    
    verification_token = serializers.CharField(write_only=True, required=True, allow_blank=True, max_length=255)
    verification_request = serializers.PrimaryKeyRelatedField(write_only=True, queryset=HospitalVerificationRequest.objects.all(), required=True)
    
    login_url = serializers.URLField(required=True, write_only=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "verification_token", "verification_request"]
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        verification_request = validated_data.pop("verification_request")
        token = validated_data.pop("verification_token")
        
        if verification_request.status != HospitalVerificationRequest.Status.APPROVED:
            raise ValidationError({"verification_request": "This request is not approved yet"})
        
        try:
            token_instance = verification_request.verification_token
        except VerificationToken.DoesNotExist:
            raise ValidationError({"verification_token": "Verification token not found"})
        
        valid, message = token_instance.verify(token)
        if not valid:
            raise ValidationError({"verification_token": message})
        
        return validated_data

    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_profile")
        validated_data['role'] = User.Role.HOSPITAL
        
        house_no = profile_data.pop("house_no", None)
        if house_no:
            profile_data["street"] = f'{house_no}, {profile_data["street"]}'
        
        user = super().create(validated_data)
        HospitalProfile.objects.create(user=user, **profile_data)
        
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
    redirect_url = serializers.URLField(required=True, write_only=True)
    
class HospitalFullInfoSerializer(serializers.ModelSerializer):
    hospital_profile = HospitalProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "hospital_profile"]
        
class HospitalBasicInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    
    class Meta:
        model = HospitalProfile
        fields = ['hin', 'name', 'email']


        