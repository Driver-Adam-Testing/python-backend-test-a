import json
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
    StartSessionStreamResponse,
)
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.encoder import UUIDEncoder
from sqlmodel import select

if TYPE_CHECKING:
    from shared.v3.app.pipelines.pipeline_response import PipelineResponse
    from shared.v3.interfaces.llm_stream_response import LlmStreamResponse


class PipelineRequest(BaseModel, ABC):
    _datasource: DataSource
    _llm_session: RuntimeLlmSession | None = None
    _datasource_changed_since_llm_session: bool = False

    def __init__(
        self,
        llm_session_id: UUID | None = None,
        page_node_id: UUID | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
        node_ids: list[UUID] | None = None,
        relative_paths: list[str] | None = None,
        **data,  # noqa: ANN003
    ) -> None:
        super().__init__(**data)
        if node_ids is not None:
            self._datasource = DataSource.from_node_ids(node_ids, organization_id)
        elif relative_paths is not None:
            self._datasource = DataSource.from_relative_paths(
                relative_paths, organization_id
            )
        elif page_node_id is not None:
            self._datasource = DataSource.from_page_id(page_node_id, organization_id)
        else:
            self._datasource = None

        with get_session() as session:
            if llm_session_id:
                self._llm_session = session.exec(
                    select(RuntimeLlmSession).where(
                        RuntimeLlmSession.id == llm_session_id
                    )
                ).first()
                if self._llm_session is not None:
                    if self._datasource is None:
                        # If the datasource is not provided, use the datasource from the llm session
                        self._datasource = DataSource.from_node_ids(
                            json.loads(self._llm_session.source_node_ids_str),
                            self._llm_session.organization_id,
                        )
                    self._datasource_changed_since_llm_session = (
                        json.dumps(self._datasource.node_ids, cls=UUIDEncoder)
                        != self._llm_session.source_node_ids_str
                    )
                    if self._datasource_changed_since_llm_session:
                        self._llm_session.source_node_ids_str = json.dumps(
                            self._datasource.node_ids, cls=UUIDEncoder
                        )
                        session.add(self._llm_session)
                        session.commit()
                        session.refresh(self._llm_session)
                else:
                    self._datasource_changed_since_llm_session = True

            if not llm_session_id or self._llm_session is None:
                self._datasource_changed_since_llm_session = True
                self._llm_session = RuntimeLlmSession(
                    organization_id=organization_id,
                    user_id=user_id,
                    source_node_ids_str=json.dumps(
                        self._datasource.node_ids, cls=UUIDEncoder
                    ),
                    page_node_id=page_node_id,
                )
                session.add(self._llm_session)
                session.commit()
                session.refresh(self._llm_session)

    @property
    def datasource(self) -> DataSource:
        if not hasattr(self, "_datasource"):
            self._datasource = DataSource.from_node_ids(
                self.node_ids,
                organization_id=self.organization_id,
            )
        return self._datasource

    @property
    def llm_session(self) -> RuntimeLlmSession:
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
            llm_session_id=self.llm_session.id,
            execution_call_id=modal.current_function_call_id(),
        )
        async for response in self._stream():
            yield response
        yield EndSessionStreamResponse(
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
