import json
from rest_framework import serializers

class CreateSoapMultipartJsonMixin:
    """
    Translates JSON strings in multipart requests into dictionaries/lists.
    """
    def to_internal_value(self, data):
        data = data.copy()
        
        json_fields = ['drug_records', 'investigations', 'problem_list', 'care_instructions', 'appointment']
        
        for field in json_fields:
            value = data.get(field)
            if isinstance(value, str):
                try:
                    data[field] = json.loads(value)
                except (ValueError, TypeError):
                    pass
        
        return super().to_internal_value(data)