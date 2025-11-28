from django.db import transaction

from rest_framework import serializers

from .models import MedicalRecord, DrugRecord, MedicalRecordAttachment
from docuhealth2.serializers import DictSerializerMixin
from patients.models import PatientProfile, SubaccountProfile
from hospitals.models import HospitalProfile, HospitalStaffProfile, VitalSigns
from appointments.models import Appointment

from hospitals.serializers.staff import HospitalStaffInfoSerilizer, HospitalStaffBasicInfoSerializer
from hospitals.serializers.hospital import HospitalBasicInfoSerializer
from hospitals.serializers.services import MedRecordsVitalSignsSerializer
from patients.serializers import PatientMedRecordsInfoSerializer

class ValueRateSerializer(serializers.Serializer):
    value = serializers.FloatField()
    rate = serializers.CharField()
    
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
        
class MedRecordAppointmentSerializer(serializers.ModelSerializer):
    staff_id = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.all(), write_only=True, source="staff") 
    staff = HospitalStaffInfoSerilizer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['staff', 'staff_id', 'scheduled_time']
        read_only_fields = ['id']

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), required=False, write_only=True)
    patient_info = PatientMedRecordsInfoSerializer(read_only=True, source="patient")
    
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), required=False)
    
    doctor = serializers.SlugRelatedField(slug_field="staff_id", queryset=HospitalStaffProfile.objects.filter(role=HospitalStaffProfile.StaffRole.DOCTOR), required=False, allow_null=True, write_only=True)
    doctor_info = HospitalStaffBasicInfoSerializer(read_only=True, source="doctor")
    
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=HospitalProfile.objects.all(), required=False, allow_null=True) 
    
    attachments = serializers.PrimaryKeyRelatedField(many=True, queryset=MedicalRecordAttachment.objects.all(), required=False, write_only=True)
    attachments_info = MedicalRecordAttachmentSerializer(many=True, read_only=True, source="attachments")
    
    drug_records = DrugRecordSerializer(many=True, required=False, allow_null=True)
    vital_signs = MedRecordsVitalSignsSerializer(required=False, allow_null=True)
    appointment = MedRecordAppointmentSerializer(required=False, allow_null=True) 
    
    hospital_info = HospitalBasicInfoSerializer(read_only=True)
    
    history = serializers.ListField(child=serializers.CharField(), required=False)
    physical_exam = serializers.ListField(child=serializers.CharField(), required=False)
    diagnosis = serializers.ListField(child=serializers.CharField(), required=False)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=False)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'hospital')
        
    @transaction.atomic()
    def create(self, validated_data):
        user = self.context['request'].user
        staff = user.hospital_staff_profile
        
        drug_records_data = validated_data.pop('drug_records', [])
        attachments_data = validated_data.pop('attachments', [])
        appointment_data = validated_data.pop('appointment', None)
        vital_signs_data = validated_data.pop('vital_signs', None)
        
        hospital = validated_data.get("hospital")
        patient = validated_data.get('patient')
        
        if vital_signs_data:
            vital_signs = VitalSigns.objects.create(patient=patient, hospital=hospital, staff=staff, **vital_signs_data)
            validated_data['vital_signs'] = vital_signs
        
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
    