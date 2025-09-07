import json
from rest_framework import serializers

class JSONFieldSerializer(serializers.Serializer):
    """
    A wrapper serializer field that safely parses JSON from request.data
    before handing it off to a nested serializer.
    """
    def __init__(self, serializer_class, many=False, **kwargs):
        self.serializer_class = serializer_class
        self.many = many
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        # If it's a JSON string, decode it
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON format")

        # Hand it off to the real serializer for validation
        serializer = self.serializer_class(data=data, many=self.many)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def to_representation(self, value):
        # Use the nested serializer for output as well
        serializer = self.serializer_class(value, many=self.many)
        return serializer.data
