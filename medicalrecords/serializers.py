from rest_framework import serializers

from .models import MedicalRecord, DrugRecord, MedicalRecordAttachment
from docuhealth2.serializers import DictSerializerMixin
from patients.models import PatientProfile, SubaccountProfile
from hospitals.models import HospitalProfile, HospitalStaffProfile
from appointments.serializers import MedRecordAppointmentSerializer
from appointments.models import Appointment

class ValueRateSerializer(serializers.Serializer):
    value = serializers.FloatField()
    rate = serializers.CharField()
    
class VitalSignsSerializer(DictSerializerMixin, serializers.Serializer):
    blood_pressure = serializers.CharField()
    temp = serializers.FloatField()
    resp_rate = serializers.FloatField()
    height = serializers.FloatField()
    weight = serializers.FloatField()
    heart_rate = serializers.FloatField()
    
class DrugRecordSerializer(serializers.ModelSerializer):
    frequency = ValueRateSerializer()
    duration = ValueRateSerializer()
    class Meta:
        model = DrugRecord
        fields = ('name', 'route', 'quantity', 'frequency', 'duration', 'created_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'medical_record')
        
class MedicalRecordAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecordAttachment
        fields = "__all__"
        read_only_fields = ('id', 'updated_at', 'file_size')

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), required=False)
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), required=False)
    doctor = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.Role.DOCTOR), required=False, allow_null=True, write_only=True)
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=False, allow_null=True) 
    attachments = serializers.PrimaryKeyRelatedField(many=True, queryset=MedicalRecordAttachment.objects.all(), required=False, write_only=True)
    
    drug_records = DrugRecordSerializer(many=True, required=False, allow_null=True)
    vital_signs = VitalSignsSerializer()
    appointment = MedRecordAppointmentSerializer(required=False, allow_null=True) 
    
    history = serializers.ListField(child=serializers.CharField(), required=False)
    physical_exam = serializers.ListField(child=serializers.CharField(), required=False)
    diagnosis = serializers.ListField(child=serializers.CharField(), required=False)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=False)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'hospital')
        
    def create(self, validated_data):
        drug_records_data = validated_data.pop('drug_records', [])
        attachments_data = validated_data.pop('attachments', [])
        appointment_data = validated_data.pop('appointment', None)
        hospital = validated_data.get("hospital")
        patient = validated_data.get('patient')
        
        medical_record = MedicalRecord.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(medical_record=medical_record, patient=patient, hospital=hospital, **drug_data)
            
        for attachment in attachments_data:
            attachment.medical_record = medical_record
            attachment.save()
            
        if appointment_data:
            print(appointment_data)
            Appointment.objects.create(patient=patient, medical_record=medical_record, hospital=hospital, **appointment_data) 
        
        return medical_record
    
class ListMedicalRecordsSerializer(serializers.ModelSerializer):
    hospital = serializers.SerializerMethodField()
    doctor = serializers.SerializerMethodField(read_only=True)
    attachments = serializers.SerializerMethodField(read_only=True)
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), required=False)
    
    drug_records = DrugRecordSerializer(many=True)
    appointment = MedRecordAppointmentSerializer() 
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'hospital')
        
    def get_hospital(self, obj):
        if obj.hospital:
            return {"hin":obj.hospital.hin, "name":obj.hospital.name, "email": obj.hospital.user.email}
        return None
    
    def get_doctor(self, obj):
        if obj.doctor:
            return {"doc_id": obj.doctor.staff_id, "firstname": obj.doctor.firstname, "lastname": obj.doctor.lastname, "specialization": obj.doctor.specialization}
        return None
    
    def get_attachments(self, obj):
        return [{"url": attachment.file.url, "filename": attachment.filename, "uploaded_at": attachment.uploaded_at, "file_size": f"{attachment.file_size} MB"} for attachment in obj.attachments.all()]
    
    def get_patient(self, obj):
        if obj.patient:
            return {"hin": obj.patient.hin, "dob": obj.patient.dob}
        return None
    
