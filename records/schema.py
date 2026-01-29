from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import SoapNoteSerializer, DrugRecordSerializer
from hospital_ops.serializers import BookAppointmentSerializer

# Full Schema Definition
CREATE_SOAP_NOTE_SCHEMA = {
    "request": {
        "multipart/form-data": inline_serializer(
            name="SoapNoteMultipartRequest",
            fields={
                # Files
                "investigations_docs": serializers.ListField(
                    child=serializers.FileField(), required=False
                ),
                # Identifiers
                "patient": serializers.CharField(help_text="Patient HIN"),
                "staff": serializers.CharField(help_text="Staff ID"),
                "vital_signs": serializers.IntegerField(required=False),
                "referred_docuhealhosp": serializers.CharField(required=False),
                
                # Nested JSON objects (Handled by Serializers)
                "drug_records": DrugRecordSerializer(many=True),
                "appointment": BookAppointmentSerializer(required=False),
                
                # JSON Lists
                "investigations": serializers.ListField(child=serializers.CharField(), required=False),
                "problems_list": serializers.ListField(child=serializers.CharField(), required=False),
                "care_instructions": serializers.ListField(child=serializers.CharField()),
                "drug_history_allergies": serializers.ListField(child=serializers.CharField(), required=False),
                "general_exam": serializers.ListField(child=serializers.CharField(), required=False),
                "systemic_exam": serializers.ListField(child=serializers.CharField(), required=False),
                "bedside_tests": serializers.ListField(child=serializers.CharField(), required=False),
                "treatment_plan": serializers.ListField(child=serializers.CharField(), required=False),
                            
                # Text Fields
                "chief_complaint": serializers.CharField(),
                "history": serializers.CharField(required=False),
                "past_med_history": serializers.CharField(required=False),
                "family_history": serializers.CharField(required=False),
                "social_history": serializers.CharField(required=False),
                "review": serializers.CharField(required=False),
                "primary_diagnosis": serializers.CharField(),
                "differential_diagnosis": serializers.CharField(required=False),
                "patient_education": serializers.CharField(required=False),
                "referred_hosp": serializers.CharField(required=False),
            }
        )
    },
    "responses": {201: SoapNoteSerializer},
}