from rest_framework import serializers

from .models import MedicalRecord, DrugRecord, MedicalRecordAttachment
from core.models import User

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
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not instance.get("appointment"):   
            rep.pop("appointment", None)
        return rep
    
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
        fiels = ('attachment')
        read_only_fields = ('id', 'uploaded_at')

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=True)
    referred_docuhealth_hosp = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=False, allow_null=True) # Chamge queryset to only hospitals
    drug_records = DrugRecordSerializer(many=True, required=False, allow_null=True)
    
    # vital_signs = VitalSignsSerializer()
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
            
    def create(self, validated_data):
        drug_records_data = validated_data.pop('drug_records', [])
        attachments_data = validated_data.pop('attachments', [])
        print(attachments_data)
        patient = validated_data.get('patient')
        
        # hospital = request.user  # add hospital creatiing the med record later
        
        medical_record = MedicalRecord.objects.create(**validated_data)
        
        for drug_data in drug_records_data:
            DrugRecord.objects.create(medical_record=medical_record, patient=patient, **drug_data) # Add hospital creatiing the med record later
            
        for attachment in attachments_data:
            MedicalRecordAttachment.objects.create(medical_record=medical_record, **attachment)
        
        return medical_record