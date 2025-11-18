from rest_framework import serializers

from hospitals.models import HospitalStaffProfile
from hospitals.serializers import HospitalStaffSerializer

from patients.models import PatientProfile

from appointments.serializers import AppointmentPatientSerializer
from appointments.models import Appointment

class ReceptionistInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = HospitalStaffProfile
        fields = ["firstname", "lastname", "phone_no", "role", "staff_id", "email"]
        
class BookAppointmentSerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    
    class Meta:
        model = Appointment
        fields = ["staff_id", "patient_hin", "type", "note", "scheduled_time", "hospital"]
        read_only_fields = ["hospital"]