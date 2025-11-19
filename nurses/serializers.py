from rest_framework import serializers

from hospitals.models import Admission

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