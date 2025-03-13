import json
from typing import TYPE_CHECKING, Optional

from anthropic.types import Message, MessageParam
from database.models_v2 import RuntimeLlmMessage
from openai.types.chat import ChatCompletionMessage, ParsedChatCompletionMessage
from pydantic import BaseModel
from shared.v3.globals.constants import PARSEABLE_CLASS_NAME
from shared.v3.interfaces.llm_message_kind import MessageKind
from shared.v3.utils.parse_response_string import (
    parse_response_string,
)

if TYPE_CHECKING:
    from shared.v3.interfaces.llm_response_type import LlmResponseType
    from shared.v3.interfaces.llm_tool import LlmTool


class LlmMessage(BaseModel):
    class ToolCallRequest(BaseModel):
        id: str
        name: str
        arguments: str
        parsed_tool: BaseModel | None = None

    class ToolCallResponse(BaseModel):
        name: str
        id: str | None

    message_kind: MessageKind
    content: str | None = None
    parsed_content: BaseModel | None = None
    tool_response: ToolCallResponse | None = None
    tool_requests: list[ToolCallRequest] = []

    @classmethod
    def from_persistent_llm_message(
        cls, runtime_llm_message: RuntimeLlmMessage
    ) -> "LlmMessage":
        return cls(**runtime_llm_message.llm_message_json)

    def to_persistent_llm_message(self) -> RuntimeLlmMessage:
        return RuntimeLlmMessage(
            llm_message_json=self.model_dump(),
            llm_message_hash=hash(self),
        )

    @classmethod
    def from_openai_parsed_chat_completion_message(
        cls, parsed_message: ParsedChatCompletionMessage
    ) -> "LlmMessage":
        tool_requests = (
            [
                cls.ToolCallRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    parsed_tool=tool_call.function.parsed_arguments,
                )
                for tool_call in parsed_message.tool_calls
            ]
            if parsed_message.tool_calls
            else []
        )

        return cls(
            message_kind=MessageKind.TOOL_CALL_REQUEST
            if tool_requests
            else MessageKind.ASSISTANT,
            content=parsed_message.content,
            tool_requests=tool_requests,
            parsed_content=parsed_message.parsed,
        )

    @classmethod
    def from_openai_chat_completion_message(
        cls,
        chat_message: ChatCompletionMessage,
        tool_types: list["LlmTool"] | None = None,
        response_type: Optional["LlmResponseType"] = None,
    ) -> "LlmMessage":
        try:
            content_as_json = parse_response_string(chat_message.content)
        except Exception:
            content_as_json = None

        tool_requests = []
        if chat_message.tool_calls:
            tool_requests = [
                cls.ToolCallRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    parsed_tool=next(
                        (
                            tool(**json.loads(tool_call.function.arguments))
                            for tool in (tool_types or [])
                            if tool.__name__ == tool_call.function.name
                        ),
                        None,
                    ),
                )
                for tool_call in chat_message.tool_calls
            ]
        elif chat_message.content and content_as_json:
            if isinstance(content_as_json, dict):
                content_as_json = [content_as_json]
            for content_json in content_as_json:
                if PARSEABLE_CLASS_NAME in content_json:
                    class_name = content_json[PARSEABLE_CLASS_NAME]
                    if tool_types:
                        for tool in tool_types:
                            if tool.__name__ == class_name:
                                tool_requests.append(
                                    cls.ToolCallRequest(
                                        id="",
                                        name=class_name,
                                        arguments=chat_message.content,
                                        parsed_tool=tool(**content_json),
                                    )
                                )
                                break

        parsed_content = None

        if response_type and not tool_requests and content_as_json:
            parsed_content = response_type(**content_as_json[0])

        message_kind = (
            MessageKind.TOOL_CALL_REQUEST if tool_requests else MessageKind.ASSISTANT
        )

        return cls(
            message_kind=message_kind,
            content=chat_message.content,
            tool_requests=tool_requests,
            parsed_content=parsed_content,
        )

    @classmethod
    def from_string(
        cls,
        string: str,
        tool_types: list["LlmTool"] | None = None,
        response_type: Optional["LlmResponseType"] = None,
    ) -> "LlmMessage":
        try:
            content_as_json = parse_response_string(string)
        except Exception:
            content_as_json = None

        if content_as_json:
            if isinstance(content_as_json, dict):
                content_as_json = [content_as_json]
            tool_requests = []
            for content_json in content_as_json:
                if PARSEABLE_CLASS_NAME in content_json:
                    class_name = content_json[PARSEABLE_CLASS_NAME]
                    if tool_types:
                        for tool in tool_types:
                            if tool.__name__ == class_name:
                                tool_requests.append(
                                    cls.ToolCallRequest(
                                        id=content_json.get("id"),
                                        name=class_name,
                                        arguments=content_json.get("arguments"),
                                        parsed_tool=tool(**content_json),
                                    )
                                )
                                break
            if tool_requests:
                return cls(
                    message_kind=MessageKind.TOOL_CALL_REQUEST,
                    tool_requests=tool_requests,
                )
        parsed_content = None
        if response_type and content_as_json:
            parsed_content = response_type(**content_as_json[0])
        return cls(
            message_kind=MessageKind.ASSISTANT,
            content=string,
            parsed_content=parsed_content,
        )

    @classmethod
    def from_anthropic_message(
        cls,
        message: Message | MessageParam,
        tool_types: list["LlmTool"] | None = None,
        response_type: Optional["LlmResponseType"] = None,
    ) -> "LlmMessage":
        """
        Creates an LlmMessage instance from an Anthropic message response.

        Args:
            message: The Anthropic message response
            tool_list: Optional list of tool types that can be used to parse tool responses
            response_type: Optional type to parse the response content into

        Returns:
            An LlmMessage instance containing the message content and any parsed data
        """
        content = ""
        if isinstance(message, Message):
            if message.content and len(message.content) > 0:
                content = message.content[0].text
        elif isinstance(message, MessageParam):
            content = message.content

        try:
            content_as_json = parse_response_string(content)
        except Exception:
            content_as_json = None

        tool_requests = []

        if tool_types and content_as_json:
            if isinstance(content_as_json, dict):
                content_as_json = [content_as_json]

            if content_as_json and tool_types:
                for content_json in content_as_json:
                    if PARSEABLE_CLASS_NAME in content_json:
                        class_name = content_json[PARSEABLE_CLASS_NAME]
                        for tool in tool_types:
                            if tool.__name__ == class_name:
                                tool_requests.append(
                                    cls.ToolCallRequest(
                                        id="",
                                        name=class_name,
                                        arguments=content,
                                        parsed_tool=tool(**content_json),
                                    )
                                )
                                break

        parsed_content = None
        if response_type and not tool_requests and content_as_json:
            try:
                parsed_content = response_type(**content_as_json[0])
            except Exception:
                parsed_content = None

        # Determine message kind based on presence of tool requests
        message_kind = (
            MessageKind.TOOL_CALL_REQUEST if tool_requests else MessageKind.ASSISTANT
        )

        return cls(
            message_kind=message_kind,
            content=content,
            tool_requests=tool_requests,
            parsed_content=parsed_content,
        )

    def print_to_console(self) -> None:
        color_map = {
            MessageKind.USER: "\033[38;5;82m",
            MessageKind.ASSISTANT: "\033[38;5;45m",
            MessageKind.DEVELOPER: "\033[38;5;196m",
            MessageKind.SYSTEM: "\033[38;5;93m",
            MessageKind.TOOL_CALL_RESPONSE: "\033[38;5;208m",
            MessageKind.TOOL_CALL_REQUEST: "\033[38;5;202m",
            MessageKind.ITERATION: "\033[38;5;214m",
            MessageKind.PARSING_DESCRIPTION: "\033[38;5;100m",
        }

        color_reset = "\033[0m"
        message_color = color_map.get(self.message_kind, "\033[94m")
        print(f"{message_color}{self.message_kind}")
        if self.tool_response:
            print(f"Tool Response: {self.tool_response}")
        if self.content:
            print(f"Content: {self.content}")
        if self.tool_requests:
            print("Tool Requests:")
            for tool_request in self.tool_requests:
                print(
                    f"    {tool_request.id} : {tool_request.name} {tool_request.arguments}"
                )
        if self.parsed_content:
            print(f"Parsed Content: \n{self.parsed_content.model_dump()}")
        print(color_reset)

    def __hash__(self) -> int:
        return hash(str([self.message_kind, self.content, self.tool_requests]))
