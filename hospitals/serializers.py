from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import HospitalProfile, HospitalInquiry, HospitalVerificationRequest, VerificationToken, HospitalStaffProfile, HospitalPatientActivity, HospitalWard, WardBed, Admission

from core.models import User
from core.serializers import BaseUserCreateSerializer

from appointments.models import Appointment
from appointments.serializers import AppointmentPatientSerializer

from patients.models import PatientProfile

class HospitalProfileSerializer(serializers.ModelSerializer):
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    class Meta:
        model= HospitalProfile
        fields = ['name', 'hin', 'street', 'city', 'state', 'country', 'house_no']
        read_only_fields = ['hin']
        
class HospitalStaffStaffInfoSerilizer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = HospitalStaffProfile
        fields = ["firstname", "lastname", "phone_no", "role", "staff_id", "email"]
        
class CreateHospitalSerializer(BaseUserCreateSerializer):
    profile = HospitalProfileSerializer(required=True, source="hospital_profile")
    
    verification_token = serializers.CharField(write_only=True, required=True, allow_blank=True, max_length=255)
    verification_request = serializers.PrimaryKeyRelatedField(write_only=True, queryset=HospitalVerificationRequest.objects.all(), required=True)
    
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
    redirect_url = serializers.URLField(required=True, allow_blank=True)
    
class HospitalStaffProfileSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = HospitalStaffProfile
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'hospital', 'staff_id', 'user']
        
    def get_is_active(self, obj):
        return obj.user.is_active
    
class TeamMemberCreateSerializer(BaseUserCreateSerializer):
    profile = HospitalStaffProfileSerializer(required=True, source="hospital_staff_profile")
    invitation_message = serializers.CharField(write_only=True, required=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ['profile', 'invitation_message']
        
    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_staff_profile")
        validated_data['role'] = User.Role.HOSPITAL_STAFF
        
        hospital = self.context['request'].user.hospital_profile
        
        user = super().create(validated_data)
        HospitalStaffProfile.objects.create(user=user, hospital=hospital, **profile_data)
        
        return user
    
class RemoveTeamMembersSerializer(serializers.Serializer):
    staff_ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=True)
    
class TeamMemberUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStaffProfile
        fields = ['role']
        
    def update(self, instance, validated_data):
        new_role = validated_data['role']

        if instance.role == new_role:
            raise serializers.ValidationError({"role": "Role already assigned"})
        
        instance.role = new_role
        instance.save(update_fields=["role"])
        
        return instance
    
class HospitalStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStaffProfile
        fields = ['staff_id', 'firstname', 'lastname', 'role', 'specialization']
    
class HospitalAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    staff = HospitalStaffSerializer(read_only=True)
    patient = AppointmentPatientSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff', 'patient', 'last_visited', 'note', 'type']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
class PatientBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'firstname', 'lastname', 'gender']
        
    
class HospitalActivitySerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffSerializer(read_only=True)
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)

    class Meta:
        model = HospitalPatientActivity
        fields = ["id", "staff", "staff_id", "patient", "patient_hin", "action", "created_at"]
        
class HospitalInfoSerializer(serializers.ModelSerializer):
    hospital_profile = HospitalProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "hospital_profile"]

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
        
class AdmissionSerializer(serializers.ModelSerializer):
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)
    
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffSerializer(read_only=True)
    
    ward = serializers.PrimaryKeyRelatedField(queryset=HospitalWard.objects.all())
    
    bed = serializers.PrimaryKeyRelatedField(queryset=WardBed.objects.all(), write_only=True)
    bed_info = WardBedSerializer(read_only=True, source="bed")
    
    class Meta:
        model = Admission
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['id', 'status', 'hospital', 'admission_date', 'discharge_date']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        ward = validated_data['ward']
        bed = validated_data['bed']
        
        if bed.status == WardBed.Status.REQUESTED:
            raise serializers.ValidationError({"bed": f"Admission to bed {bed.bed_number} has been requested already. Revoke the request or choose another bed"})
        
        if bed.status == WardBed.Status.OCCUPIED:
            raise serializers.ValidationError({"bed": f"Bed {bed.bed_number} is occupied"})
        
        if not bed.ward == ward:
            raise serializers.ValidationError({"ward": "Bed not available in this ward"})
        
        if not ward.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"ward": "Ward with provided ID not found"})
        
        return validated_data