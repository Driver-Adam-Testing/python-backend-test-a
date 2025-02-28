import json
from abc import ABC

from shared.v3.globals.constants import (
    FORMAT_RESPONSE_AS_JSON_f_class_name__example_json__docstring,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_parseable import LlmParseable


class LlmResponseType(LlmParseable, ABC):
    """
    This is a base class for all response types.
    """

    def to_markdown(self) -> str:
        raise str(self)

    @classmethod
    def to_parsing_description_message(cls) -> LlmMessage:
        """
        Returns the docstring and an example of the JSON it would take to generate it.

        Returns:
            LlmMessage: A message that can be used to generate the response type.
        """
        example_dict = cls._generate_example_for_model()
        example_json = json.dumps(example_dict, indent=4)

        return LlmMessage(
            content=FORMAT_RESPONSE_AS_JSON_f_class_name__example_json__docstring.format(
                class_name=cls.__name__,
                example_json=example_json,
                docstring=cls.__doc__,
            ),
            message_kind=MessageKind.PARSING_DESCRIPTION,
        )
