import enum

from pydantic import BaseModel


class LlmStreamResponseKind(str, enum.Enum):
    RESPONSE_CHUNK = "RESPONSE"
    TOOL_STATUS_UPDATE = "TOOL_STATUS_UPDATE"
    ERROR = "ERROR"
    END = "END"
    RESPONSE_FULL = "RESPONSE_FULL"


class LlmStreamResponse(BaseModel):
    kind: LlmStreamResponseKind
    content: str | None = None
    full_message: BaseModel | None = None
