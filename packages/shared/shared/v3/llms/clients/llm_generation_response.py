from typing import Any

from pydantic import BaseModel

# FUCK! this is where I left off.


class LlmToolCall(BaseModel):
    id: str
    parsed_tool: Any
    name: str
    type: str

    @classmethod
    def from_parsed_function_tool_call(cls, parsed_tool_call: Any) -> "LlmToolCall":
        return cls(
            id=parsed_tool_call.id,
            parsed_tool=parsed_tool_call.function.parsed_arguments,
            name=parsed_tool_call.function.name,
            type=parsed_tool_call.type,
        )


class LlmGenerationResponse(BaseModel):
    tool_calls: list[LlmToolCall] = []
    content: str | None
    parsed_response: Any
    function_call: Any

    @classmethod
    def from_parsed_chat_completion_message(
        cls, parsed_message: Any
    ) -> "LlmGenerationResponse":
        tool_calls = [
            LlmToolCall.from_parsed_function_tool_call(tool_call)
            for tool_call in parsed_message.tool_calls
        ]
        return cls(
            tool_calls=tool_calls,
            content=parsed_message.content,
            parsed_response=parsed_message.parsed,
            function_call=parsed_message.function_call,
        )
