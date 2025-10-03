from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import PatientProfile, SubaccountProfile
from core.models import User
from core.serializers import BaseUserCreateSerializer
from appointments.models import Appointment
from hospitals.models import DoctorProfile, HospitalProfile

from docuhealth2.serializers import StrictFieldsMixin

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by', 'hin']
        read_only_fields = ['hin']
        
class CreatePatientSerializer(BaseUserCreateSerializer):
    profile = PatientProfileSerializer(required=True, source="patient_profile")
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "house_no"]

    def create(self, validated_data):
        profile_data = validated_data.pop("patient_profile")
        validated_data['role'] = User.Role.PATIENT
        
        user = super().create_user(validated_data)
        PatientProfile.objects.create(user=user, **profile_data)
        
        return user
    
class UpdatePatientProfileSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename']
        
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
        
        if profile_data:
            profile = instance.patient_profile
            for attr, value in profile_data.items():
                if value is not None:
                    setattr(profile, attr, value)
            profile.save()

        instance.save()
        return instance

class CreateSubaccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = SubaccountProfile
        fields = ['firstname', 'lastname', 'middlename', 'dob', 'gender', 'hin', 'user']
        read_only_fields = ['hin' ]
    
    def create(self, validated_data):
        user = User.objects.create(role="subaccount")
        validated_data['user'] = user
            
        return super().create(validated_data)
        
class UpgradeSubaccountSerializer(serializers.ModelSerializer):
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), write_only=True)
    
    phone_num = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta:
        model = User
        fields = ['email', 'street', 'city', 'state', 'country', 'password', 'house_no', 'phone_num', 'subaccount']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get('email')
        
        existing_user = User.objects.filter(email=email).exists()
        if existing_user:
            raise ValidationError("A user with this email already exists.")
        
        return validated_data
        
    def create(self, validated_data):
        house_no = validated_data.pop('house_no', None)
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'
            
        subaccount_profile = validated_data.pop('subaccount')
        phone_num = validated_data.pop('phone_num')
        password = validated_data.pop('password')
        
        subaccount_user = subaccount_profile.user
        validated_data['role'] = 'patient'
        
        patient_profile_data = {
            "firstname": subaccount_profile.firstname, 
            "lastname": subaccount_profile.lastname,
            "middlename": subaccount_profile.middlename,
            "dob": subaccount_profile.dob,
            "gender": subaccount_profile.gender,
            "phone_num": phone_num
        }
        
        subaccount_user.set_password(password)
        for field, value in validated_data.items():
            setattr(subaccount_user, field, value)
            
        subaccount_user.save()
        
        PatientProfile.objects.create(user=subaccount_user, **patient_profile_data)
        
        return subaccount_user
    
class DoctorAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['doc_id', 'firstname', 'lastname']
        
class HospitalAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalProfile
        fields = ['hin', 'firstname', 'lastname']
    
class PatientAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    doctor = DoctorAppointmentSerializer(read_only=True)
    hospital = HospitalAppointmentSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'doctor', 'hospital', 'last_visited']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
# class 
        
            