from abc import ABC, abstractmethod

from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.messages.llm_message_kind import MessageKind


class LlmToolContext(BaseModel):
    datascope: DataScope
    llm_config: LlmConfig
    tool_call_id: str | None = None


class LlmToolReference(BaseModel):
    content: str


class LlmToolResponse(BaseModel, ABC):
    @abstractmethod
    def to_message(self) -> LlmMessage:
        raise NotImplementedError()

    def to_references(self) -> list[LlmToolReference]:
        raise NotImplementedError()


class LlmToolResponseError(LlmToolResponse):
    error_message: str
    tool_call_id: str

    def to_message(self) -> LlmMessage:
        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL,
            message_id=self.tool_call_id,
            content=f"Error in {self.tool_call_id}: {self.error_message}",
        )

    def to_references(self) -> list[LlmToolReference]:
        return []


class LlmTool(BaseModel, ABC):
    _tool_context: LlmToolContext

    @abstractmethod
    def execute(self, **kwargs: any) -> LlmToolResponse:
        raise NotImplementedError()
