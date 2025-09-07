from rest_framework import serializers

from .models import MedicalRecord, DrugRecord, MedicalRecordAttachment
from core.models import User

import json

class ValueRateSerializer(serializers.Serializer):
    value = serializers.FloatField()
    rate = serializers.CharField()
    
class VitalSignsSerializer(serializers.Serializer):
    blood_pressure = serializers.CharField()
    temp = serializers.FloatField()
    resp_rate = serializers.FloatField()
    height = serializers.FloatField()
    weight = serializers.FloatField()
    heart_rate = serializers.FloatField()
    
class AppointmentSerializer(serializers.Serializer):
    date = serializers.DateField()
    time = serializers.TimeField()
    
    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        return {
            "date": validated["date"].isoformat(),
            "time": validated["time"].isoformat() if hasattr(validated["time"], "isoformat") else str(validated["time"]),
        }
        
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
        fields = ('file', )
        read_only_fields = ('id', 'uploaded_at', 'medical_record')

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=True)
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=False, allow_null=True) # Change queryset to only hospitals
    drug_records = DrugRecordSerializer(many=True, required=False, allow_null=True)
    attachments = serializers.PrimaryKeyRelatedField(many=True, queryset=MedicalRecordAttachment.objects.all(), required=False)
    
    vital_signs = VitalSignsSerializer()
    appointment = AppointmentSerializer(required=False, allow_null=True, default=None)
    
    history = serializers.ListField(child=serializers.CharField(), required=False)
    physical_exam = serializers.ListField(child=serializers.CharField(), required=False)
    diagnosis = serializers.ListField(child=serializers.CharField(), required=False)
    treatment_plan = serializers.ListField(child=serializers.CharField(), required=False)
    care_instructions = serializers.ListField(child=serializers.CharField(), required=False)
    
    attachments = MedicalRecordAttachmentSerializer(many=True, required=False)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'hospital')
        
    # def to_internal_value(self, data):
    #     ret = super().to_internal_value(data)

    #     for field in ["drug_records", "appointment", "vital_signs"]:
    #         raw_value = data.get(field)
    #         if raw_value:
    #             try:
    #                 ret[field] = json.loads(raw_value)
    #             except Exception:
    #                 raise serializers.ValidationError(
    #                     {field: "Invalid JSON format"}
    #                 )

    #     return ret
            
    def create(self, validated_data):
        print(validated_data)
        drug_records_data = validated_data.pop('drug_records', [])
        attachments_data = validated_data.pop('attachments', [])
        # print(attachments_data, drug_records_data)
        patient = validated_data.get('patient')
        
        # hospital = request.user  # add hospital creatiing the med record later
        
        medical_record = MedicalRecord.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(medical_record=medical_record, patient=patient, **drug_data) # Add hospital creatiing the med record later
            
        for attachment in attachments_data:
            MedicalRecordAttachment.objects.create(medical_record=medical_record, **attachment)
        
        return medical_record