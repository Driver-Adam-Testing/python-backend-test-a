import json
from collections.abc import AsyncGenerator
from uuid import UUID

from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_stream_response import (
    LlmStreamResponse,
    LlmStreamResponseKind,
)
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.encoder import UUIDEncoder


async def run_chat_pipeline(
    llm_session_id: UUID,
    message_history: LlmMessageHistory,
    datasource: DataSource,
    llm_client: LlmClient = LlmClient.o3_mini(),
) -> AsyncGenerator[LlmStreamResponse, None]:
    yield json.dumps(
        LlmStreamResponse(
            kind=LlmStreamResponseKind.START_SESSION,
            session_id=llm_session_id,
        ).model_dump(),
        cls=UUIDEncoder,
    )
    async for chunk in llm_client.multi_shot_stream(
        tool_types=[HybridSearchTool],
        message_history=message_history,
        datasource=datasource,
    ):
        yield json.dumps(chunk.model_dump())
    yield json.dumps(
        LlmStreamResponse(
            kind=LlmStreamResponseKind.END_SESSION,
            session_id=llm_session_id,
        ).model_dump(),
        cls=UUIDEncoder,
    )
