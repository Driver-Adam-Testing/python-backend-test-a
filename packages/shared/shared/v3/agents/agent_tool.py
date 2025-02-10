from abc import ABC, abstractmethod

from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.utils.parseable import LlmParseable


class LlmToolContext(BaseModel):
    datascope: DataScope
    llm_config: LlmConfig
    tool_call_id: str | None = None


class LlmToolReference(BaseModel):
    content: str


class LlmToolResponse(BaseModel, ABC):
    content: str | None = None
    references: list[LlmToolReference] = []

    @abstractmethod
    def to_message(self) -> LlmMessage:
        raise NotImplementedError()

    def to_references(self) -> list[LlmToolReference]:
        raise NotImplementedError()


class LlmTool(LlmParseable, ABC):
    _tool_context: LlmToolContext

    @abstractmethod
    def execute(self, **kwargs: any) -> LlmToolResponse:
        raise NotImplementedError()
