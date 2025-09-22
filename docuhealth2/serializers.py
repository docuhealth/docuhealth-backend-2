from rest_framework import serializers

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




