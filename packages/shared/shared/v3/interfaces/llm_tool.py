from abc import ABC, abstractmethod

from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.utils.parseable import LlmParseable
from shared.v3.utils.references import Reference


class LlmToolContext(BaseModel):
    datascope: DataScope
    llm_config: LlmConfig
    tool_call_id: str | None = None


class LlmTool(LlmParseable, ABC):
    _tool_context: LlmToolContext
    _references: list[Reference] | None = None

    @property
    def references(self) -> list[Reference]:
        return self._references

    @abstractmethod
    def execute(self, tool_context: LlmToolContext) -> LlmMessage:
        raise NotImplementedError()

    @abstractmethod
    def to_message(self) -> LlmMessage:
        raise NotImplementedError()
