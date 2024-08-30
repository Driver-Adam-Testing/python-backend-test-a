from abc import ABC, abstractmethod

from pydantic import BaseModel


class ToolStrict(BaseModel, ABC):
    @abstractmethod
    def execute(self, agent, **kwargs):
        pass

    @classmethod
    def anthropic_tool_schema(cls):
        """
        Create a schema that conforms to the parameters of the ToolStrict subclass.
        """
        properties = {}
        required = []

        for field_name, field in cls.model_fields.items():
            field_info = {
                "type": "string"
                if field.annotation == str
                else "number"
                if field.annotation in [int, float]
                else "boolean"
                if field.annotation == bool
                else "object",
                "description": field.description or f"The {field_name} field.",
            }
            if hasattr(field, "enum") and field.enum:
                field_info["enum"] = list(field.enum)
                field_info["type"] = "string"
            if hasattr(field, "list") and field.list:
                field_info["type"] = "array"
                field_info["items"] = {"type": "string"}
            if field.default is not None:
                field_info["default"] = field.default
            elif field.default is None and field.default_factory is None:
                required.append(field_name)
            properties[field_name] = field_info

        schema = {"type": "object", "properties": properties, "required": required}
        return schema
