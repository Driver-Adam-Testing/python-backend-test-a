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
        tool_list: list[type] | None = None,
        response_type: type | None = None,
    ) -> "LlmMessage":
        content_as_json_list: list[dict] = []
        with contextlib.suppress(json.JSONDecodeError):
            trimmed_content = (
                chat_message.content.strip()
                .removeprefix("```json")
                .removesuffix("```")
                .strip()
            )
            content_json = json.loads(trimmed_content)
            if isinstance(content_json, list):
                content_as_json_list = content_json
            else:
                content_as_json_list = [content_json]

        tool_requests = []

        if chat_message.tool_calls:
            tool_requests = [
                cls.ToolCallRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    parsed_tool=next(
                        (
                            tool.parse_raw(tool_call.function.arguments)
                            for tool in (tool_list or [])
                            if tool.__name__ == tool_call.function.name
                        ),
                        None,
                    ),
                )
                for tool_call in chat_message.tool_calls
            ]

        elif content_as_json_list:
            for content_json in content_as_json_list:
                if "class_name" in content_json:
                    class_name = content_json["class_name"]
                    if tool_list:
                        for tool in tool_list:
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

        if response_type and not tool_requests and content_as_json_list:
            parsed_content = response_type(**content_as_json_list[0])

        message_kind = (
            MessageKind.TOOL_CALL_REQUEST if tool_requests else MessageKind.ASSISTANT
        )

        return cls(
            message_kind=message_kind,
            content=chat_message.content,
            tool_requests=tool_requests,
            parsed_content=parsed_content,
        )
