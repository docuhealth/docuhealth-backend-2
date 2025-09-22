from rest_framework import serializers

from .models import Appointment

from hospitals.models import DoctorProfile

class MedRecordAppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.SlugRelatedField(slug_field="hin", queryset=DoctorProfile.objects.all(), write_only=True) 
    scheduled_time = serializers.DateTimeField(write_only=True, required=True)
    
    class Meta:
        model = Appointment
        fields = ('doctor', 'scheduled_time')
        read_only_fields = ('id', 'updated_at', 'created_at', 'medical_record', 'hospital', 'patient', 'status')