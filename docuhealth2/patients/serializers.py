from rest_framework import serializers
from .models import PatientProfile

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'emergency']  