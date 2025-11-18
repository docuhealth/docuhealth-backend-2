from rest_framework import serializers

from .models import Appointment
from hospitals.models import HospitalProfile
from patients.models import PatientProfile

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'doctor', 'hospital', 'last_visited']
        read_only_fields = fields
        
class AppointmentHospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalProfile
        fields = ['hin', 'name']
        
class AppointmentPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'firstname', 'lastname', 'gender']
        
