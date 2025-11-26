from rest_framework import serializers

from hospitals.models import Admission, HospitalStaffProfile
from appointments.models import Appointment

class AssignAppointmentToDoctorSerializer(serializers.ModelSerializer):
    doctor_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    
    class Meta:
        model = Appointment
        fields = ['note', 'type', 'scheduled_time', 'doctor_id']