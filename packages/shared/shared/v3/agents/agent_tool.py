from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.llms.config.llm_config import LlmConfig
from shared.v3.messages.llm_message import LlmMessage
from shared.v3.utils.parseable import LlmParseable


class LlmToolContext(BaseModel):
    datascope: DataScope
    llm_config: LlmConfig
    tool_call_id: str | None = None


class ToolReference(BaseModel):
    content: str
    score: float
    version_display_name: str
    relative_path: str
    version_id: UUID
    node_id: UUID
    metadata: dict

    def __hash__(self) -> int:
        return hash(self.content + str(self.version_id))

    def __eq__(self, other: "ToolReference"):
        return self.content + str(self.version_id) == other.content + str(
            other.version_id
        )


class LlmTool(LlmParseable, ABC):
    _tool_context: LlmToolContext
    _references: list[ToolReference] | None = None

    @property
    def references(self) -> list[ToolReference]:
        return self._references

    @abstractmethod
    def execute(self, tool_context: LlmToolContext) -> LlmMessage:
        raise NotImplementedError()

    @abstractmethod
    def to_message(self) -> LlmMessage:
        raise NotImplementedError()
