import json
from abc import ABC, abstractmethod

from shared.v3.globals.constants import (
    FORMAT_TOOL_CALL_REQUEST_f_class_name__example_json__docstring,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_parseable import LlmParseable
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.references import ReferenceSet


class LlmTool(LlmParseable, ABC):
    """
    A tool that can be called by an LLM.
    """

    class LlmToolStatusString(str):
        """
        A status message for a tool.
        """

        def __str__(self) -> str:
            return self.value

    _tool_call_id: str | None = None
    _tool_datasource: DataSource | None = None

    _references: ReferenceSet = ReferenceSet(references=[])

    @property
    def tool_call_id(self) -> str | None:
        return self._tool_call_id

    @property
    def datasource(self) -> DataSource | None:
        return self._tool_datasource

    @property
    def references(self) -> ReferenceSet:
        return self._references

    @property
    def status(self) -> LlmToolStatusString:
        return f"Tool called: {self.__class__.__name__}\n"

    def execute(
        self,
        tool_call_id: str,
        datasource: DataSource,
    ) -> LlmMessage:
        self._tool_call_id = tool_call_id
        self._tool_datasource = datasource
        self._execute()
        return self.to_tool_call_response_message()

    @abstractmethod
    def _execute(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def to_tool_call_response_message(self) -> LlmMessage:
        raise NotImplementedError()

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
            content=FORMAT_TOOL_CALL_REQUEST_f_class_name__example_json__docstring.format(
                class_name=cls.__name__,
                example_json=example_json,
                docstring=cls.__doc__,
            ),
            message_kind=MessageKind.PARSING_DESCRIPTION,
        )
