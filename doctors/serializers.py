from rest_framework import serializers

from patients.models import PatientProfile
from patients.serializers import PatientFullInfoSerializer

from hospitals.serializers.services import VitalSignsSerializer
from medicalrecords.serializers import DrugRecordSerializer

class PatientMedInfoSerializer(serializers.Serializer): 
    patient_info = PatientFullInfoSerializer()
    latest_vitals = VitalSignsSerializer(allow_null=True)
    ongoing_drugs = DrugRecordSerializer(many=True)
    
