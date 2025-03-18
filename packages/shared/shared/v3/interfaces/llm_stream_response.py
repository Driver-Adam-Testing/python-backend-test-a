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


class StartSessionStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.START_SESSION
    llm_session_id: UUID


class EndSessionStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.END_SESSION
    llm_session_id: UUID


class ResponseChunkStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.RESPONSE_CHUNK
    content: str


class ToolStatusUpdateStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.TOOL_STATUS_UPDATE
    content: str


class ErrorStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.ERROR
    error_message: str


class ResponseFullStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.RESPONSE_FULL
    content: str
