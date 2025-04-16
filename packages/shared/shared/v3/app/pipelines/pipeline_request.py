from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from shared.v3 import LlmClient
from shared.v3.utils.datasource import DataSource

if TYPE_CHECKING:
    from shared.v3.app.pipelines.pipeline_response import PipelineResponse
    from shared.v3.interfaces.llm_stream_response import LlmStreamResponse


class PipelineRequest(BaseModel, ABC):
    _datasource: DataSource
    node_ids: list[UUID] | None = None
    organization_id: str | None = None

    @property
    def datasource(self) -> DataSource:
        if not hasattr(self, "_datasource"):
            self._datasource = DataSource.from_node_ids(
                self.node_ids,
                organization_id=self.organization_id,
            )
        return self._datasource

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineRequest":
        return cls(**data)

    @abstractmethod
    def run(self, client: LlmClient = None) -> "PipelineResponse":
        pass

    @abstractmethod
    async def stream(
        self, client: LlmClient = None
    ) -> AsyncGenerator["LlmStreamResponse", None]:
        pass
