from rest_framework import serializers

from .models import Appointment
from core.models import User

class MedRecordAppointmentSerializer(serializers.ModelSerializer):
    doctor = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), source="doctor.user") # Change this when hin is removed from user model, remeber to add role="doctor"
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('id', 'uploaded_at', 'medical_record', 'hospital', 'patient', 'status')