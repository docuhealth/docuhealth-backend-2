from rest_framework import serializers
from .models import PatientProfile
from medicalrecords.serializers import MedicalRecordSerializer

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by']
        
# class MedicalRecordDashboardSerializer(MedicalRecordSerializer):
#     patient_firstname = serializers.CharField(source="patient.profile.firstname", read_only=True)
#     patient_lastname = serializers.CharField(source="patient.profile.lastname", read_only=True)
#     patient_middlename = serializers.CharField(source="patient.profile.middlename", read_only=True)
#     patient_hin = serializers.CharField(source="patient.hin", read_only=True)  

#     class Meta(MedicalRecordSerializer.Meta):
#         fields = MedicalRecordSerializer.Meta.fields + (
#             "patient_firstname",
#             "patient_lastname",
#             "patient_middlename",
#             "patient_hin",
#         )