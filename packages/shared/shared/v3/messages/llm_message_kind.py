from enum import Enum


class MessageKind(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    SYSTEM = "system"
    TOOL_CALL = "tool"
