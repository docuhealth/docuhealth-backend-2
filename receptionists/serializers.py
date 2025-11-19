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
        
class UpdatePasswordView(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        old_password = validated_data['old_password']
        user = self.context['request'].user
        
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        
        return validated_data