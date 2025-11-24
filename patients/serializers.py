from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import PatientProfile, SubaccountProfile
from core.models import User
from core.serializers import BaseUserCreateSerializer
from appointments.models import Appointment
from appointments.serializers import AppointmentHospitalSerializer

from docuhealth2.serializers import StrictFieldsMixin

from hospitals.serializers import HospitalStaffSerializer

class PatientProfileSerializer(serializers.ModelSerializer):
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    email = serializers.EmailField(read_only=True, source="user.email")
    
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by', 'hin', 'street', 'city', 'state', 'country', 'house_no', 'email']
        read_only_fields = ['hin']
        
class PatientSerializer(BaseUserCreateSerializer):
    profile = PatientProfileSerializer(required=True, source="patient_profile")
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile"]

    def create(self, validated_data):
        profile_data = validated_data.pop("patient_profile")
        validated_data['role'] = User.Role.PATIENT
        
        house_no = profile_data.pop("house_no", None)
        if house_no:
            profile_data["street"] = f'{house_no}, {profile_data["street"]}'
        
        user = super().create(validated_data)
        PatientProfile.objects.create(user=user, **profile_data)
        
        return user
    
class UpdatePatientProfileSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        exclude = ['is_deleted', 'deleted_at', 'created_at', 'user', 'hin', 'id_card_generated', 'paystack_cus_code', 'referred_by', 'emergency']
        
class UpdatePatientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    profile = UpdatePatientProfileSerializer(required=False)  
    
    class Meta:
        model = User
        fields = ['email', 'password', 'profile', 'updated_at']  
        read_only_fields = ['updated_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get('email', None)
        
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        
        profile_data = validated_data.get('profile')
        if profile_data:
            profile_serializer = PatientProfileSerializer(
                instance=self.instance.patient_profile,
                data=profile_data,
                partial=True  
            )
            profile_serializer.is_valid(raise_exception=True)
            validated_data['profile'] = profile_serializer.validated_data

        return validated_data
        
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        if 'email' in validated_data:
            instance.email = validated_data['email']

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            
        instance.updated_at = timezone.now()
        
        fields = []
        if profile_data:
            profile = instance.patient_profile
            for attr, value in profile_data.items():
                if value is not None:
                    fields.append(attr)
                    setattr(profile, attr, value)
            profile.save(update_fields=fields)

        instance.save()
        return instance

class CreateSubaccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = SubaccountProfile
        exclude = ['is_deleted', 'deleted_at', 'created_at', 'updated_at', 'id_card_generated', 'parent']
        read_only_fields = ['hin' ]
    
    def create(self, validated_data):
        user = User.objects.create(role="subaccount")
        validated_data['user'] = user
            
        return super().create(validated_data)
        
class UpgradeSubaccountSerializer(serializers.ModelSerializer):
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), write_only=True)
    
    phone_num = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'phone_num', 'subaccount']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get('email')
        
        existing_user = User.objects.filter(email=email).exists()
        if existing_user:
            raise ValidationError("A user with this email already exists.")
        
        return validated_data
        
    def create(self, validated_data):
        subaccount_profile = validated_data.pop('subaccount')
        
        phone_num = validated_data.pop('phone_num')
        password = validated_data.pop('password')
        
        subaccount_user = subaccount_profile.user
        validated_data['role'] = User.Role.PATIENT
        
        patient_profile_data = {
            "firstname": subaccount_profile.firstname, 
            "lastname": subaccount_profile.lastname,
            "middlename": subaccount_profile.middlename,
            "dob": subaccount_profile.dob,
            "gender": subaccount_profile.gender,
            "phone_num": phone_num,
            
            "id_card_generated": subaccount_profile.id_card_generated
        }
        
        subaccount_user.set_password(password)
        for field, value in validated_data.items():
            setattr(subaccount_user, field, value)
            
        subaccount_user.save()
        
        PatientProfile.objects.create(user=subaccount_user, **patient_profile_data)
        
        return subaccount_user
    
class PatientAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    staff = HospitalStaffSerializer(read_only=True)
    hospital = AppointmentHospitalSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff', 'hospital', 'last_visited']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
class PatientEmergencySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'emergency']
        read_only_fields = ['hin']
        
class GeneratePatientIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'id_card_generated']
        read_only_fields = ['hin']
        
class GenerateSubaccountIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubaccountProfile
        fields = ['hin', 'id_card_generated']
        read_only_fields = ['hin']
        
class PatientBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'firstname', 'lastname', 'gender']
        
