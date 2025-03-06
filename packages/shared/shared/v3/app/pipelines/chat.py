from collections.abc import AsyncGenerator

from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.interfaces.llm_message import LlmMessage
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.utils.datasource import DataSource


async def run_chat_pipeline(
    message_history: LlmMessageHistory,
    datasource: DataSource,
) -> AsyncGenerator[str, None] | AsyncGenerator[LlmMessage, None]:
    llm_client = LlmClient.o3_mini()
    async for chunk in llm_client.multi_shot_stream(
        tool_types=[HybridSearchTool],
        message_history=message_history,
        datasource=datasource,
    ):
        yield chunk
