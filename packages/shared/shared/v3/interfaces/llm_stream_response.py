import enum
import json
from uuid import UUID

from pydantic import BaseModel
from shared.v3.utils.encoder import UUIDEncoder


class LlmStreamResponseKind(str, enum.Enum):
    RESPONSE_CHUNK = "RESPONSE_CHUNK"
    TOOL_STATUS_UPDATE = "TOOL_STATUS_UPDATE"
    ERROR = "ERROR"
    END_SESSION = "END_SESSION"
    START_SESSION = "START_SESSION"
    RESPONSE_FULL = "RESPONSE_FULL"


class LlmStreamResponse(BaseModel):
    kind: LlmStreamResponseKind

    def to_sse(self) -> str:
        """
        Convert the response to an SSE-formatted string.
        """
        # Use json.dumps with your custom encoder if necessary.
        payload = json.dumps(self.model_dump(), cls=UUIDEncoder)
        return f"data: {payload}\n\n"

    def __str__(self) -> str:
        return self.to_sse()

    def encode(self, *args: any, **kwargs: any) -> bytes:
        return self.to_sse().encode(*args, **kwargs)


class StartSessionStreamResponse(LlmStreamResponse):
    kind: LlmStreamResponseKind = LlmStreamResponseKind.START_SESSION
    llm_session_id: UUID
    execution_call_id: str | None = None


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
