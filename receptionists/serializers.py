from rest_framework import serializers

from hospitals.models import HospitalStaffProfile
from hospitals.serializers import HospitalStaffInfoSerilizer, PatientBasicInfoSerializer

from patients.models import PatientProfile

from appointments.models import Appointment

class BookAppointmentSerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ["staff_id", "patient_hin", "patient", "staff", "type", "note", "scheduled_time", "hospital"]
        read_only_fields = ["hospital"]