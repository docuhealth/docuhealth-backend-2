from drf_spectacular.extensions import OpenApiSerializerFieldExtension
from drf_spectacular.plumbing import (
    build_basic_type,
    build_array_type,
    build_object_type
)
from structured.fields import StructuredJSONField
from typing import get_origin, get_args

class StructuredJSONFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "structured.fields.StructuredJSONField"

    def map_serializer_field(self, auto_schema, direction):
        schema = getattr(self.target, "schema", None)

        if schema is None:
            return build_basic_type(object)  # fallback

        return self._convert_schema(schema)

    def _convert_schema(self, schema):
        """
        Recursively convert schema to OpenAPI types.
        Handles List[str], List[int], TypedDict-like, dataclass, nested structures.
        """
        origin = get_origin(schema)

        # Handle lists
        if origin == list or origin == tuple:
            inner_type = get_args(schema)[0]
            return build_array_type(self._convert_schema(inner_type))

        # Handle dict-like / TypedDict / dataclass
        if hasattr(schema, "__annotations__"):
            props = {}
            for field_name, field_type in schema.__annotations__.items():
                props[field_name] = self._convert_schema(field_type)
            return build_object_type(properties=props)

        # Map basic types
        if schema == str:
            return build_basic_type(str)
        if schema == int:
            return build_basic_type(int)
        if schema == float:
            return build_basic_type(float)
        if schema == bool:
            return build_basic_type(bool)

        # Fallback
        return build_basic_type(object)
