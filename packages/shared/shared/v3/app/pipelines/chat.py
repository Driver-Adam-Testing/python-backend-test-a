from __future__ import annotations

from typing import TYPE_CHECKING

from database.db import get_session
from database.models import RuntimeLlmMessageHistory, RuntimeLlmSession
from database.models_enums import LlmPipelineKind
from shared.v3 import LlmClient, LlmMessage, LlmMessageHistory, MessageKind
from shared.v3.app.pipelines.pipeline_request import PipelineRequest
from shared.v3.app.pipelines.pipeline_response import PipelineResponse
from shared.v3.app.static.messages.copy_editor_messages import CopyEditorSystemMessage
from shared.v3.app.static.messages.driver_app_messages import (
    ChatContextMessage,
    ContentStructureMessage,
    DriverApplicationMessage,
    HowDriverWorksMessage,
    PromptGuidelinesMessage,
)
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.globals.datasource_messages import (
    DataSourceMessage,
    DataSourceSystemMessage,
    DataSourceTuningSystemMessage,
)
from sqlmodel import select

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Sequence

    from shared.v3.interfaces.llm_stream_response import LlmStreamResponse

__all__: Sequence[str] = [
    "ChatPipelineRequest",
    "ChatPipelineResponse",
]


class ChatPipelineResponse(PipelineResponse):
    """Typed response for the chat pipeline (inherits `final_response` & `references`)."""


class ChatPipelineRequest(PipelineRequest):
    """Pipeline request for the `/chat` endpoint with history persistence."""

    user_prompt: str

    def _get_or_create_message_history(self) -> LlmMessageHistory:
        """Return the complete message history *with* the new user message.

        1. Load the existing chat history from the DB if it exists.
        2. If no history exists, initialize a new one with standard system messages.
        3. Append the current `user_prompt` to the history.
        """
        db = get_session()

        history: LlmMessageHistory | None = None
        runtime_session: RuntimeLlmSession = self.llm_session

        with db as session:
            chat_history_id = session.exec(
                select(RuntimeLlmMessageHistory.id).where(
                    RuntimeLlmMessageHistory.llm_session_id == runtime_session.id,
                    RuntimeLlmMessageHistory.pipeline_kind == LlmPipelineKind.CHAT,
                )
            ).first()
            if chat_history_id is not None:
                history = LlmMessageHistory.from_db(message_history_id=chat_history_id)

        if history is None:
            history = LlmMessageHistory(
                messages=[
                    DriverApplicationMessage(),
                    ContentStructureMessage(),
                    HowDriverWorksMessage(),
                    DataSourceSystemMessage(),
                    DataSourceTuningSystemMessage(),
                    PromptGuidelinesMessage(),
                    CopyEditorSystemMessage(),
                    ChatContextMessage(),
                    DataSourceMessage.from_context(self.datasource),
                ],
                llm_session_id=runtime_session.id,
                pipeline_kind=LlmPipelineKind.CHAT,
            )
        if self._datasource_changed_since_llm_session:
            history.add_message(DataSourceMessage.from_context(self.datasource))
        history.add_message(
            LlmMessage(message_kind=MessageKind.USER, content=self.user_prompt)
        )

        return history

    def _run(self, client: LlmClient = LlmClient.gpt_4_1()) -> ChatPipelineResponse:
        history = self._get_or_create_message_history()
        information_response, called_tools = client.multi_shot(
            message_history=history,
            tool_types=[HybridSearchTool],
            iterations=3,
            datasource=self.datasource,
        )

        return ChatPipelineResponse(
            final_response=information_response.content,
            references=list({ref for tool in called_tools for ref in tool.references}),
        )

    async def _stream(
        self,
        client: LlmClient = LlmClient.gpt_4_1(),
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        history = self._get_or_create_message_history()

        async for chunk in client.multi_shot_stream(
            message_history=history,
            tool_types=[HybridSearchTool],
            iterations=3,
            datasource=self.datasource,
        ):
            yield chunk
