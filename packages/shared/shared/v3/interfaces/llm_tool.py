import asyncio
import inspect
import json
import threading
from abc import ABC, abstractmethod
from functools import partial

from shared.v3.globals.constants import (
    FORMAT_TOOL_CALL_REQUEST_f_class_name__example_json__docstring,
)
from shared.v3.globals.glossary import TOOL_ERROR_MESSAGE
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
    _error_message: str | None = None
    one_sentence_rationale_for_calling_the_tool: str | None = None

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
    def error_message(self) -> str | None:
        return self._error_message

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

        def target() -> None:
            try:
                self._execute()
            except Exception as e:
                self._error_message = str(e)

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=25)

        if thread.is_alive():
            print(
                f"Execution of {self.__class__.__name__, self.tool_call_id} timed out after 25 seconds."
            )
            self._error_message = f"Execution of {self.__class__.__name__, self.tool_call_id} timed out after 25 seconds."
            return LlmMessage(
                content=f"{TOOL_ERROR_MESSAGE.wrap(self._error_message)}",
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name=self.__class__.__name__
                ),
            )

        if self._error_message:
            return LlmMessage(
                content=f"{TOOL_ERROR_MESSAGE.wrap(self._error_message)}",
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name=self.__class__.__name__
                ),
            )

        return self.to_tool_call_response_message()

    async def aexecute(
        self,
        tool_call_id: str,
        datasource: DataSource | None = None,
    ) -> LlmMessage:
        """
        Non-blocking wrapper around `execute`.

        • If a future tool replaces `execute` with an `async def`, we await it.
        • Otherwise we off-load the current sync implementation (which itself
          runs a secondary thread) to the event-loop executor so the loop stays
          free for other I/O.
        """
        try:
            if inspect.iscoroutinefunction(self.execute):
                return await self.execute(tool_call_id, datasource)

            loop = asyncio.get_running_loop()
            fn = partial(self.execute, tool_call_id=tool_call_id, datasource=datasource)
            return await loop.run_in_executor(None, fn)
        except Exception as e:
            error_message = f"Error during execution: {e!s}"
            return LlmMessage(
                content=error_message,
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                tool_response=LlmMessage.ToolCallResponse(
                    id=tool_call_id, name=self.__class__.__name__
                ),
            )

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
