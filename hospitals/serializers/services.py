from rest_framework import serializers

from hospitals.models import HospitalStaffProfile, HospitalWard, WardBed, Admission, VitalSigns, VitalSignsRequest, HospitalPatientActivity

from appointments.models import Appointment
from appointments.serializers import AppointmentPatientSerializer

from patients.models import PatientProfile
from patients.serializers import PatientFullInfoSerializer, PatientBasicInfoSerializer

from .staff import HospitalStaffInfoSerilizer, HospitalStaffBasicInfoSerializer
from .hospital import HospitalBasicInfoSerializer

class HospitalAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    patient = AppointmentPatientSerializer(read_only=True)
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff', 'patient', 'last_visited', 'note', 'type', 'hospital_info']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
class WardBedSerializer(serializers.ModelSerializer):
    class Meta:
        model = WardBed  
        fields = ['bed_number', 'status', 'id']   
        read_only_fields = ['id']
    
class WardSerializer(serializers.ModelSerializer):
    beds = WardBedSerializer(many=True, read_only=True)
    available_beds = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = HospitalWard
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['available_beds', 'id', 'hospital']
        
class WardBasicInfoSerializer(serializers.ModelSerializer):
    available_beds = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = HospitalWard
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['available_beds', 'id', 'hospital']
        
class WardNameSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = HospitalWard
        fields = ['id', 'name']
        read_only_fields = fields
        
class AdmissionSerializer(serializers.ModelSerializer):
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientFullInfoSerializer(read_only=True)
    
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    
    ward = serializers.PrimaryKeyRelatedField(queryset=HospitalWard.objects.all(), write_only=True)
    ward_info = WardNameSerializer(read_only=True, source="ward")
    
    bed = serializers.PrimaryKeyRelatedField(queryset=WardBed.objects.all(), write_only=True)
    bed_info = WardBedSerializer(read_only=True, source="bed")
    
    class Meta:
        model = Admission
        exclude = ['is_deleted', 'deleted_at', 'created_at']
        read_only_fields = ['id', 'status', 'hospital', 'admission_date', 'discharge_date']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        ward = validated_data['ward']
        bed = validated_data['bed']
        
        if bed.status == WardBed.Status.REQUESTED:
            raise serializers.ValidationError({"bed": f"Admission to bed {bed.bed_number} has been requested already. Revoke the request or choose another bed"})
        
        if bed.status == WardBed.Status.OCCUPIED:
            raise serializers.ValidationError({"bed": f"Bed {bed.bed_number} is occupied"})
        
        if not bed.ward == ward:
            raise serializers.ValidationError({"ward": "Bed not available in this ward"})
        
        if not ward.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"ward": "Ward with provided ID not found"})
        
        return validated_data
    
class VitalSignsRequestSerializer(serializers.ModelSerializer):
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientFullInfoSerializer(read_only=True)
    
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.NURSE), write_only=True)
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    class Meta:
        model = VitalSignsRequest
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'processed_at', 'status', 'hospital']
        
class VitalSignsViaRequestSerializer(serializers.ModelSerializer):
    request = serializers.PrimaryKeyRelatedField(write_only=True, queryset=VitalSignsRequest.objects.all(), required=True)
    
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['hospital', 'patient', 'staff', 'created_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        vital_signs_request = validated_data['request']
        staff = self.context['request'].user.hospital_staff_profile
        hospital = staff.hospital
        
        if vital_signs_request.status == VitalSignsRequest.Status.PROCESSED:
            raise serializers.ValidationError({"request": f"This vital signs request has been processed already"})
        
        if vital_signs_request.staff != staff:
            raise serializers.ValidationError({"request": "This request was not assigned to this staff"})
        
        if not vital_signs_request.hospital == hospital:
            raise serializers.ValidationError({"request": "Request with provided ID not found"})
        
        return validated_data
    
class VitalSignsSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    staff = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['hospital', 'created_at']
        
class MedRecordsVitalSignsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSigns
        exclude = ['is_deleted', 'deleted_at', 'staff', 'patient', 'hospital', 'created_at', 'id']
        
class HospitalActivitySerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)

    class Meta:
        model = HospitalPatientActivity
        fields = ["id", "staff", "staff_id", "patient", "patient_hin", "action", "created_at"]
        
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