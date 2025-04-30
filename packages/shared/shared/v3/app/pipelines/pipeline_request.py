from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

import modal
from database.db import get_session
from database.models_v2 import RuntimeLlmSession
from pydantic import BaseModel
from shared.v3 import LlmClient
from shared.v3.interfaces.llm_stream_response import (
    EndSessionStreamResponse,
    LlmStreamResponse,
    LlmStreamResponseKind,
    StartSessionStreamResponse,
)
from shared.v3.utils.datasource import DataSource

if TYPE_CHECKING:
    from shared.v3.app.pipelines.pipeline_response import PipelineResponse
    from shared.v3.interfaces.llm_stream_response import LlmStreamResponse


class PipelineRequest(BaseModel, ABC):
    _datasource: DataSource
    node_ids: list[UUID] | None = None
    organization_id: str | None = None
    user_id: str | None = None

    @property
    def datasource(self) -> DataSource:
        if not hasattr(self, "_datasource"):
            self._datasource = DataSource.from_node_ids(
                self.node_ids,
                organization_id=self.organization_id,
            )
        return self._datasource

    _llm_session: RuntimeLlmSession | None = None

    @property
    def llm_session(self) -> RuntimeLlmSession:
        if self._llm_session is None:
            with get_session() as session:
                self._llm_session = RuntimeLlmSession(
                    organization_id=self.organization_id,
                    user_id=self.user_id,
                )
                session.add(self._llm_session)
                session.commit()
                session.refresh(self._llm_session)
        return self._llm_session

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineRequest":
        return cls(**data)

    def run(self, client: LlmClient = None) -> "PipelineResponse":
        return self._run()

    async def stream(
        self, client: LlmClient = None
    ) -> AsyncGenerator["LlmStreamResponse", None]:
        yield StartSessionStreamResponse(
            kind=LlmStreamResponseKind.START_SESSION,
            llm_session_id=self.llm_session.id,
            execution_call_id=modal.current_function_call_id(),
        )
        async for response in self._stream():
            yield response
        yield EndSessionStreamResponse(
            kind=LlmStreamResponseKind.END_SESSION,
            llm_session_id=self.llm_session.id,
        )

    @abstractmethod
    def _run(self, client: LlmClient = None) -> "PipelineResponse":
        raise NotImplementedError("This pipeline does not support this method")

    @abstractmethod
    async def _stream(
        self, client: LlmClient = None
    ) -> AsyncGenerator["LlmStreamResponse", None]:
        raise NotImplementedError("This pipeline does not support this method")
