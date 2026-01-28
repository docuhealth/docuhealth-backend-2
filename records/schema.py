from drf_spectacular.utils import OpenApiExample

from .serializers import SoapNoteSerializer

CREATE_SOAP_NOTE_SCHEMA = {
    "description": (
        "Create a comprehensive SOAP note. Note: Since this is a multipart/form-data request, "
        "complex fields like 'drug_records', 'investigations', 'problem_list', and 'care_instructions' "
        "must be sent as JSON strings if your client does not support nested form-data."
    ),
    "request": {
        "multipart/form-data": {
            "type": "object",
            "properties": {
                # File field
                "investigations_docs": {
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                    "description": "Upload one or more investigation documents (PDF, Images)."
                },
                # Identifiers
                "patient": {"type": "string", "description": "Patient HIN"},
                "staff": {"type": "string", "description": "Staff ID"},
                "vital_signs": {"type": "integer", "description": "ID of the VitalSigns record"},
                
                # Nested JSON Strings
                "drug_records": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/DrugRecord"},
                    "description": "JSON string representing list of drug prescriptions."
                },
                "appointment": {
                    "type": "object",
                    "description": "JSON string representing appointment details."
                },
                
                # List fields
                "investigations": {"type": "array", "items": {"type": "string"}},
                "problems_list": {"type": "array", "items": {"type": "string"}},
                "care_instructions": {"type": "array", "items": {"type": "string"}},
                
                # Text fields
                "chief_complaint": {"type": "string"},
                "history": {"type": "string"},
                "past_med_history": {"type": "string"},
                "family_history": {"type": "string"},
                "social_history": {"type": "string"},
                "primary_diagnosis": {"type": "string"},
                "treatment_plan": {"type": "string"},
            },
            "required": ["patient", "staff", "chief_complaint", "primary_diagnosis", "treatment_plan", "care_instructions", "drug_records"]
        }
    },
    "responses": {201: SoapNoteSerializer},
    "examples": [
        OpenApiExample(
            'Multipart Payload Example',
            summary='How to format the drug_records string',
            value={
                "patient": "PAT-12345",
                "staff": "STF-999",
                "chief_complaint": "Persistent cough",
                "drug_records": '[{"name": "Amoxicillin", "quantity": 1, "route": "Oral", "frequency": {"morning": 1}, "duration": {"days": 7}}]',
                "care_instructions": '["Drink plenty of water", "Rest for 3 days"]',
                "primary_diagnosis": "Upper Respiratory Infection"
            }
        )
    ]
}