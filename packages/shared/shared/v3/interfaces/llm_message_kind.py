from enum import Enum


class MessageKind(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system"
    TOOL_CALL_RESPONSE = "tool_call_response"
    TOOL_CALL_REQUEST = "tool_call_request"
    ITERATION = "iteration"
    PARSING_DESCRIPTION = "parsing_description"
