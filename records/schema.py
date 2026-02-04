from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import SoapNoteSerializer, DrugRecordSerializer, DischargeFormSerializer, SoapNoteAdditionalNotesSerializer
from hospital_ops.serializers import RecordAppointmentSerializer

CREATE_SOAP_NOTE_SCHEMA = {
    "request": {
        "application/json": inline_serializer(
            name="SoapNoteMultipartRequest",
            fields={
                # Files
                "investigation_docs": serializers.ListField(
                    child=serializers.FileField(), required=False
                ),
                # Identifiers
                "patient": serializers.CharField(help_text="Patient HIN"),
                "vital_signs": serializers.IntegerField(required=False),
                "referred_docuhealhosp": serializers.CharField(required=False),
                
                # Nested JSON objects (Handled by Serializers)
                "drug_records": DrugRecordSerializer(many=True),
                "appointment": RecordAppointmentSerializer(required=False),
                "additional_notes": SoapNoteAdditionalNotesSerializer(many=True, required=False, read_only=True),
                
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
                "other_history": serializers.CharField(required=False),
                "history_of_complain": serializers.CharField(required=False),
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


CREATE_DISCHARGE_FORM_SCHEMA = {
    "request": {
        "application/json": inline_serializer(
            name="DischargeFormMultipartRequest",
            fields={
                "investigation_docs": serializers.ListField(
                    child=serializers.FileField(), required=False
                ),
                
                "admission": serializers.IntegerField(),
                
                "drug_records": DrugRecordSerializer(many=True),
                "follow_up_appointment": RecordAppointmentSerializer(required=False),
                
                # JSON Lists
                "diagnosis": serializers.ListField(child=serializers.CharField(), required=False),
                "treatment_plan": serializers.ListField(child=serializers.CharField()),
                "care_instructions": serializers.ListField(child=serializers.CharField(), required=False),
                            
                # Text Fields
                "chief_complaint": serializers.CharField(),
                "condition_on_discharge": serializers.CharField()
            }
        )
    },
    "responses": {201: DischargeFormSerializer},
}