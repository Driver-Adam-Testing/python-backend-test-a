import enum
from uuid import UUID

from pydantic import BaseModel


class LlmStreamResponseKind(str, enum.Enum):
    RESPONSE_CHUNK = "RESPONSE_CHUNK"
    TOOL_STATUS_UPDATE = "TOOL_STATUS_UPDATE"
    ERROR = "ERROR"
    END_SESSION = "END_SESSION"
    START_SESSION = "START_SESSION"
    RESPONSE_FULL = "RESPONSE_FULL"


class LlmStreamResponse(BaseModel):
    kind: LlmStreamResponseKind
    content: str | None = None
    session_id: UUID | None = None
