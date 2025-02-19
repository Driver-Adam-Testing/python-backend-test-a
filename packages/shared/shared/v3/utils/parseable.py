import enum
import json
from abc import ABC
from typing import Union, get_args, get_origin

from pydantic import BaseModel
from shared.v3.static.messages.global_message_constants import IMPORTANT


class LlmParseable(BaseModel, ABC):
    """
    A base model that can be used to auto-generate instructions for an LLM
    to produce valid JSON for subclasses.
    """

    parsed_classname: str = None

    def __init__(self, **data: any) -> None:
        super().__init__(**data)
        if self.parsed_classname is None:
            self.parsed_classname = self.__class__.__name__

    @staticmethod
    def _is_enum(type_: any) -> bool:
        """
        Check if `type_` is an Enum subclass without error on non-class type hints.
        """
        return isinstance(type_, type) and issubclass(type_, enum.Enum)

    @classmethod
    def _generate_example_value(cls, field_type: any) -> any:
        """
        Recursively generate an example value for the given field_type.
        Handles:
          - Union / Optional
          - List / Tuple
          - Enums
          - Nested BaseModels
          - Basic types (int, float, bool, str)
          - Fallback to a generic string otherwise.
        """
        origin = get_origin(field_type)

        # Handle Unions (like Optional[X] or Union[X, Y, ...])
        if origin is Union:
            args = get_args(field_type)
            # Pick the first arg that isn't NoneType
            non_none_type = next((arg for arg in args if arg is not type(None)), None)
            if non_none_type is None:
                return None
            return cls._generate_example_value(non_none_type)

        # Handle List or Tuple
        if origin in (list, tuple, list, tuple):
            (item_type,) = get_args(field_type) or (str,)
            return [cls._generate_example_value(item_type)]

        # Handle Enum
        if cls._is_enum(field_type):
            return next(iter(field_type)).value  # pick the first enumerated value

        # Handle BaseModel
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Generate example for the model and include the field_type's docstring in comments
            example = field_type._generate_example_for_model()
            if field_type.__doc__:
                example["_docstring"] = field_type.__doc__
            return example

        # Basic built-in types
        if field_type is int:
            return 123
        if field_type is float:
            return 3.14
        if field_type is bool:
            return True
        if field_type is str:
            return "example_string"

        # Fallback
        return "example_value"

    @classmethod
    def _generate_example_for_model(cls) -> dict:
        """
        Generate a dictionary with example values for all fields in the model.
        Pydantic 2 uses `model_fields` which returns a dict of {field_name: FieldInfo}.
        The `class_name` field is included so that the generated JSON can be parsed
        to the correct tool class or response_type.
        """
        example_data = {}
        for field_name, field_info in cls.model_fields.items():
            field_type = field_info.annotation
            if field_name == "parsed_classname":
                example_data[field_name] = cls.__name__
            else:
                example_data[field_name] = cls._generate_example_value(field_type)
        return example_data

    @classmethod
    def to_instruction_response_string(cls) -> str:
        # TODO: validate that cls is a response type first.
        """
        Returns the docstring and an example of the JSON it would take to generate it.

        Returns:
            str: A string that can be used to generate the response type.
        """
        example_dict = cls._generate_example_for_model()
        example_json = json.dumps(example_dict, indent=4)
        return (
            f"Format your response as a JSON object that can be parsed "
            f"as {cls.__name__}(pydantic.BaseModel)\n\n"
            f"{cls.__doc__}\n"
            f'{IMPORTANT} Set the "parsed_classname" field to "{cls.__name__}"\n'
            f"Example JSON object:\n"
            f"{example_json}\n"
        )

    @classmethod
    def to_instruction_tool_string(cls) -> str:
        # TODO validate that cls is a tool first.
        """
        Returns the docstring and an example of the JSON it would take to generate it.

        Returns:
            str: A string that can be used to generate the response type.
        """
        example_dict = cls._generate_example_for_model()
        example_json = json.dumps(example_dict, indent=4)

        return (
            f"Format your response as a JSON object that can be parsed "
            f"as {cls.__name__}(pydantic.BaseModel)\n"
            f"{IMPORTANT} To respond with this tool, Set the 'parsed_classname' field to '{cls.__name__}'.\n"
            f"{cls.__doc__}\n"
            f"Example JSON object:\n"
            f"{example_json}\n"
        )
