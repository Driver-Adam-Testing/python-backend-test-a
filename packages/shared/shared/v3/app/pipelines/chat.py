from collections.abc import AsyncGenerator
from uuid import UUID

from pydantic import BaseModel
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.interfaces.llm_stream_response import (
    EndSessionStreamResponse,
    LlmStreamResponse,
    LlmStreamResponseKind,
    StartSessionStreamResponse,
)
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.references import ReferenceSet


async def run_chat_pipeline(
    llm_session_id: UUID,
    message_history: LlmMessageHistory,
    datasource: DataSource,
    llm_client: LlmClient = LlmClient.o3_mini(),
) -> AsyncGenerator[LlmStreamResponse, None]:
    """
    Run the chat pipeline.

    :param llm_session_id: The ID of the LLM session.
    :param message_history: The message history.
    :param datasource: The datasource.
    :param llm_client: The LLM client.
    """
    yield StartSessionStreamResponse(
        kind=LlmStreamResponseKind.START_SESSION,
        llm_session_id=llm_session_id,
    ).to_sse()
    async for chunk in llm_client.multi_shot_stream(
        tool_types=[HybridSearchTool],
        message_history=message_history,
        datasource=datasource,
    ):
        yield chunk.to_sse()

    yield EndSessionStreamResponse(
        kind=LlmStreamResponseKind.END_SESSION,
        llm_session_id=llm_session_id,
    ).to_sse()


class SyncChatPipelineResponse(BaseModel):
    message: str
    references: ReferenceSet


def run_chat_pipeline_sync(
    message_history: LlmMessageHistory,
    datasource: DataSource,
    llm_client: LlmClient = LlmClient.o3_mini(),
) -> SyncChatPipelineResponse:
    """
    Run the chat pipeline synchronously.

    :param message_history: The message history.
    :param datasource: The datasource.
    :param llm_client: The LLM client.
    :return: The final response as a string.
    """
    message, tools = llm_client.multi_shot(
        tool_types=[HybridSearchTool],
        message_history=message_history,
        datasource=datasource,
    )
    return SyncChatPipelineResponse(
        message=message.content,
        references=ReferenceSet.from_list_of_reference_sets(
            [t.references for t in tools]
        ),
    )
