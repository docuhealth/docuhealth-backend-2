from rest_framework import serializers

from .models import Appointment

from hospitals.models import DoctorProfile

class MedRecordAppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.SlugRelatedField(slug_field="doc_id", queryset=DoctorProfile.objects.all()) 
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'scheduled_time']
        read_only_fields = ['id']
        
class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'doctor', 'hospital', 'last_visited']
        read_only_fields = fields