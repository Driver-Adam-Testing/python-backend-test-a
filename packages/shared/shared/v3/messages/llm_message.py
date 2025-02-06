from pydantic import BaseModel
from shared.v3.messages.llm_message_kind import MessageKind


class LlmMessage(BaseModel):
    message_kind: MessageKind
    content: str | None = None
    message_id: str | None = None
    name: str | None = None
    refusal: str | None = None
    role: str | None = None
    audio: str | None = None
    function_call: str | None = None
    tool_calls: list[dict] = []
    parsed: str | None = None
