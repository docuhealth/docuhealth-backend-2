from rest_framework import serializers

from .models import HospitalPatientActivity, Appointment, HandOverLog

from accounts.models import PatientProfile, HospitalStaffProfile
from accounts.serializers import PatientFullInfoSerializer, PatientBasicInfoSerializer, HospitalStaffBasicInfoSerializer, HospitalStaffInfoSerilizer

from organizations.serializers import HospitalBasicInfoSerializer
from organizations.models import HospitalProfile

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
        last_completed_appointment = Appointment.objects.filter(patient=obj.patient, status=Appointment.Status.COMPLETED, scheduled_time__lt=obj.scheduled_time).order_by('-scheduled_time').first()
        return last_completed_appointment.scheduled_time if last_completed_appointment else None
    
        
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
    class Meta:
        model = Appointment
        fields = ['id', 'status', 'scheduled_time', 'doctor', 'hospital', 'last_visited']
        read_only_fields = fields
        
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
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", source="staff", queryset=HospitalStaffProfile.objects.all(), write_only=True)
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    patient_hin = serializers.SlugRelatedField(slug_field="hin", source="patient", queryset=PatientProfile.objects.all(), write_only=True)
    patient = PatientBasicInfoSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ["staff_id", "patient_hin", "patient", "staff", "type", "note", "scheduled_time", "hospital"]
        read_only_fields = ["hospital"]
        
class HandOverLogSerializer(serializers.ModelSerializer):
    to_nurse = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.NURSE), write_only=True)
    to_nurse_info = HospitalStaffBasicInfoSerializer(source="to_nurse", read_only=True)
    
    from_nurse_info = HospitalStaffBasicInfoSerializer(source="from_nurse", read_only=True)
    
    class Meta:
        model = HandOverLog
        fields = ["id", "from_nurse_info", "to_nurse", "to_nurse_info", "items_transferred", "handover_appointments", "handover_patients", "created_at"]
        read_only_fields = ["id", "from_nurse_info", "to_nurse_info", "created_at", "items_transferred"]
        

