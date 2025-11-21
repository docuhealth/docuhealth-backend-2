from rest_framework import serializers

from hospitals.models import Admission, HospitalStaffProfile
from appointments.models import Appointment

class ConfirmAdmissionSerializer(serializers.Serializer):
    def validate(self, attrs):
        admission = self.context['admission']
        staff = self.context['request'].user.hospital_staff_profile
        hospital = staff.hospital
        
        if admission.ward != staff.ward:
            raise serializers.ValidationError({"detail": "You are not assigned to this ward."})
        
        if admission.hospital != hospital:
            raise serializers.ValidationError({"detail": "Admission with the provided ID does not exist"})
        
        if admission.status != Admission.Status.PENDING:
            raise serializers.ValidationError({"detail": "This admission is either already confirmed or cancelled or the patient has been discharged"})
        
        return  super().validate(attrs)
    
class AssignAppointmentToDoctorSerializer(serializers.ModelSerializer):
    doctor_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    
    class Meta:
        model = Appointment
        fields = ['note', 'type', 'scheduled_time', 'doctor_id']