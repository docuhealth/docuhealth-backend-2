from rest_framework import serializers
import json
from django.http import QueryDict

class DictSerializerMixin:
    def to_representation(self, instance):
        return instance
    
class StrictFieldsMixin:
    """
    Ensures that serializers only accept known fields.
    Raises a ValidationError if unknown fields are provided.
    """
    def to_internal_value(self, data):
        allowed_fields = set(self.fields.keys())
        provided_fields = set(data.keys())
        unknown_fields = provided_fields - allowed_fields

        if unknown_fields:
            raise serializers.ValidationError(
                {field: f"Invalid field: {field}" for field in unknown_fields}
            )

        return super().to_internal_value(data)
    
class MultipartJsonMixin:
    """
    A reusable mixin to parse JSON strings in multipart/form-data requests.
    Looks for a 'multipart_json_fields' attribute on the Serializer Meta class.
    """
    def to_internal_value(self, data):
        if isinstance(data, QueryDict):
            standard_data = data.dict()
        else:
            standard_data = data.copy() if hasattr(data, 'copy') else dict(data)

        meta = getattr(self, 'Meta', None)
        json_fields = getattr(meta, 'multipart_json_fields', [])

        for field in json_fields:
            value = standard_data.get(field)
            if value and isinstance(value, str):
                try:
                    standard_data[field] = json.loads(value)
                except (ValueError, TypeError) as e:
                    print(f"Mixin JSON Parse Error [{field}]: {e}")
                    pass
        
        return super().to_internal_value(standard_data)




