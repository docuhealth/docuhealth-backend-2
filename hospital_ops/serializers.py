from rest_framework import serializers

from .models import HospitalPatientActivity, Appointment, HandOverLog

from accounts.models import PatientProfile, HospitalStaffProfile
from accounts.serializers import PatientFullInfoSerializer, PatientBasicInfoSerializer, HospitalStaffBasicInfoSerializer, HospitalStaffInfoSerilizer

from organizations.serializers import HospitalBasicInfoSerializer
from organizations.models import HospitalProfile

from facility.models import HospitalWard, WardBed
from facility.serializers import WardBedSerializer, WardNameSerializer

from records.models import Admission
# from records.serializers import AdmissionSerializer

class HospitalAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    patient = PatientFullInfoSerializer(read_only=True)
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff', 'patient', 'last_visited', 'note', 'type', 'hospital_info']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        return getattr(obj, 'last_visited', None)
    
class HospitalActivitySerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)

    class Meta:
        model = HospitalPatientActivity
        fields = ["id", "staff", "staff_id", "patient", "patient_hin", "action", "created_at"]
        
class AssignAppointmentToDoctorSerializer(serializers.ModelSerializer):
    doctor_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    
    class Meta:
        model = Appointment
        fields = ['note', 'type', 'scheduled_time', 'doctor_id']
        
class AppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    
    staff_info = HospitalStaffBasicInfoSerializer(read_only=True, source="staff")
    hospital_info  = HospitalBasicInfoSerializer(read_only=True, source="hospital")
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff_info', 'hospital_info', 'last_visited']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
class RecordAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['type', 'note', 'scheduled_time']
        read_only_fields = ['created_at', 'updated_at', 'id', 'status']
        
class AppointmentHospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalProfile
        fields = ['hin', 'name']
        
class AppointmentPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'firstname', 'lastname', 'gender']
        
class PatientAppointmentSerializer(serializers.ModelSerializer):
    last_visited = serializers.SerializerMethodField(read_only=True)
    staff = HospitalStaffBasicInfoSerializer(read_only=True)
    hospital = AppointmentHospitalSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'staff', 'hospital', 'last_visited']
        read_only_fields = fields
        
    def get_last_visited(self, obj):
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
class BookAppointmentSerializer(serializers.ModelSerializer):
    staff = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff_info = HospitalStaffInfoSerilizer(read_only=True, source="staff")
    
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    patient_info = PatientBasicInfoSerializer(read_only=True, source="patient")
    
    class Meta:
        model = Appointment
        fields = ["staff_info", "patient_info", "patient", "staff", "type", "note", "scheduled_time", "hospital"]
        read_only_fields = ["hospital"]
        
class HandOverLogSerializer(serializers.ModelSerializer):
    to_nurse = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.NURSE), write_only=True)
    to_nurse_info = HospitalStaffBasicInfoSerializer(source="to_nurse", read_only=True)
    
    from_nurse_info = HospitalStaffBasicInfoSerializer(source="from_nurse", read_only=True)
    
    class Meta:
        model = HandOverLog
        fields = ["id", "from_nurse_info", "to_nurse", "to_nurse_info", "items_transferred", "handover_appointments", "handover_patients", "created_at"]
        read_only_fields = ["id", "from_nurse_info", "to_nurse_info", "created_at", "items_transferred"]
        
class TransferPatientToWardSerializer(serializers.Serializer):
    admission = serializers.PrimaryKeyRelatedField(queryset=Admission.objects.filter(status=Admission.Status.ACTIVE))
    new_ward = serializers.PrimaryKeyRelatedField(queryset=HospitalWard.objects.all(), write_only=True)
    new_bed = serializers.PrimaryKeyRelatedField(queryset=WardBed.objects.all(), write_only=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        admission = validated_data['admission']
        patient = admission.patient
        ward = validated_data['new_ward']
        bed = validated_data['new_bed']
        
        if not admission.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"admission": "Admission with the provided ID does not exist"})
        
        if admission.patient != patient:
            raise serializers.ValidationError({"admission": "Admission does not belong to the specified patient"})
        
        if admission.status != Admission.Status.ACTIVE:
            raise serializers.ValidationError({"admission": "This admission is not confirmed, cancelled or the patient has been discharged"})
        
        if bed.status == WardBed.Status.OCCUPIED:
            raise serializers.ValidationError({"bed": f"Bed {bed.bed_number} is occupied"})
        
        if not bed.ward == ward:
            raise serializers.ValidationError({"ward": "Bed not available in this ward"})
        
        if not ward.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"ward": "Ward with provided ID not found"})
        
        return validated_data
    
    def get_admission_info(self, obj):
        from records.serializers import AdmissionSerializer
        
        admission = obj.admission
        return AdmissionSerializer(admission).data
    
class DischargePatientSerializer(serializers.Serializer):
    admission = serializers.PrimaryKeyRelatedField(queryset=Admission.objects.filter(status=Admission.Status.ACTIVE))
    discharge_summary = serializers.CharField()
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        admission = validated_data['admission']
        
        if not admission.hospital == self.context['request'].user.hospital_staff_profile.hospital:
            raise serializers.ValidationError({"admission": "Admission with the provided ID does not exist"})
        
        if admission.status != Admission.Status.ACTIVE:
            raise serializers.ValidationError({"admission": "This admission is not active"})
        
        return validated_data
        

