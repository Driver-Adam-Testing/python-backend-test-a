import contextlib
import json

from openai.types.chat import ChatCompletionMessage, ParsedChatCompletionMessage
from pydantic import BaseModel
from shared.v3.messages.llm_message_kind import MessageKind


class LlmMessage(BaseModel):
    class ToolCallRequest(BaseModel):
        id: str
        name: str
        arguments: str
        parsed_tool: BaseModel | None = None

    class ToolCallResponse(BaseModel):
        id: str
        name: str

    message_kind: MessageKind
    content: str | None = None
    parsed_content: BaseModel | None = None
    tool_response: ToolCallResponse | None = None
    tool_requests: list[ToolCallRequest] = []

    @classmethod
    def from_parsed_chat_completion_message(
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
    def from_chat_completion_message(
        cls,
        chat_message: ChatCompletionMessage,
        tool_list: list[type] | None = None,
        response_type: type | None = None,
    ) -> "LlmMessage":
        # Could merge with o series and only use tool_calls if they exist.
        json_parsed_content = None
        if chat_message.content:
            with contextlib.suppress(json.JSONDecodeError):
                trimmed_content = (
                    chat_message.content.strip()
                    .removeprefix("```json")
                    .removesuffix("```")
                    .strip()
                )
                json_parsed_content = json.loads(trimmed_content)
        tool_requests = (
            [
                cls.ToolCallRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    parsed_tool=next(
                        (
                            tool.parse_raw(tool_call.function.arguments)
                            for tool in tool_list
                            if tool.__name__ == tool_call.function.name
                        ),
                        None,
                    ),
                )
                for tool_call in chat_message.tool_calls
            ]
            if chat_message.tool_calls
            else []
        )
        parsed_content = None
        if response_type and not tool_requests:
            parsed_content = response_type(**json_parsed_content)
        if tool_list and chat_message.content:
            for tool in tool_list:
                if tool.__name__ in chat_message.content:
                    parsed_content = tool.parse_raw(chat_message.content)
                    break
        return cls(
            message_kind=MessageKind.TOOL_CALL_REQUEST
            if tool_requests
            else MessageKind.ASSISTANT,
            content=chat_message.content,
            tool_requests=tool_requests,
            parsed_content=parsed_content,
        )

    @classmethod
    def from_chat_completion_message_o_series(
        cls,
        chat_message: ChatCompletionMessage,
        tool_list: list[type] | None = None,
        response_type: type | None = None,
    ) -> "LlmMessage":
        json_parsed_content = None
        with contextlib.suppress(json.JSONDecodeError):
            trimmed_content = (
                chat_message.content.strip()
                .removeprefix("```json")
                .removesuffix("```")
                .strip()
            )
            json_parsed_content = json.loads(trimmed_content)
        tool_requests = []
        if json_parsed_content and "class_name" in json_parsed_content:
            class_name = json_parsed_content["class_name"]
            if tool_list:
                for tool in tool_list:
                    if tool.__name__ == class_name:
                        tool_requests.append(
                            cls.ToolCallRequest(
                                id="",
                                name=class_name,
                                arguments=chat_message.content,
                                parsed_tool=tool(**json_parsed_content),
                            )
                        )
                        break

        parsed_content = None
        if response_type and not tool_requests:
            parsed_content = response_type(**json_parsed_content)

        return cls(
            message_kind=MessageKind.TOOL_CALL_REQUEST
            if tool_requests
            else MessageKind.ASSISTANT,
            content=chat_message.content,
            tool_requests=tool_requests,
            parsed_content=parsed_content,
        )
