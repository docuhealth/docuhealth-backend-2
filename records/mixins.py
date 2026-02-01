import json
from rest_framework import serializers

class CreateSoapMultipartJsonMixin:
    def to_internal_value(self, data):
        standard_data = data.dict()
        
        json_fields = [
            'drug_records', 'appointment', 'investigations', 
            'problems_list', 'care_instructions', 'drug_history_allergies',
            'general_exam', 'systemic_exam', 'bedside_tests', 'treatment_plan'
        ]
        
        for field in json_fields:
            value = standard_data.get(field)
            if value and isinstance(value, str):
                try:
                    standard_data[field] = json.loads(value)
                    print(f"DEBUG: {field} type: {type(standard_data[field])}")
                except (ValueError, TypeError) as e:
                    print(f"JSON Parse Error in field {field}: {e}")
                    pass
        
        return super().to_internal_value(standard_data)