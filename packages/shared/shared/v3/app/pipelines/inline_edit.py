import uuid
from collections.abc import AsyncGenerator

from shared.v3 import LlmClient, LlmMessageHistory
from shared.v3.app.pipelines.abbreviate_page_content import (
    abbreviate_page_content,
)
from shared.v3.app.pipelines.pipeline_request import PipelineRequest
from shared.v3.app.pipelines.pipeline_response import PipelineResponse
from shared.v3.app.static.messages.copy_editor_messages import (
    CopyEditorSystemMessage,
)
from shared.v3.app.static.messages.inline_edit_messages import (
    InlineEditSystemMessage,
    InlineEditToolUseMessage,
    InlineEditUserMessage,
)
from shared.v3.app.static.messages.software_expertise import SoftwareExpertiseMessage
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.globals.datasource_messages import DataSourceMessage
from shared.v3.globals.global_messages import GlobalSystemMessage
from shared.v3.interfaces.llm_stream_response import (
    EndSessionStreamResponse,
    LlmStreamResponse,
    LlmStreamResponseKind,
    StartSessionStreamResponse,
)


class InlineEditPipelineResponse(PipelineResponse):
    pass


class InlineEditPipelineInput(PipelineRequest):
    user_prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    selected_text: str

    def run(
        self, client: LlmClient = LlmClient.o3_mini()
    ) -> InlineEditPipelineResponse:
        abbreviated_page_content = abbreviate_page_content(
            user_prompt=self.user_prompt,
            page_content_before_cursor=self.page_content_before_cursor,
            page_content_after_cursor=self.page_content_after_cursor,
        )
        information_response, called_tools = client.multi_shot(
            message_history=LlmMessageHistory(
                messages=[
                    GlobalSystemMessage(),
                    SoftwareExpertiseMessage(),
                    InlineEditSystemMessage(),
                    InlineEditToolUseMessage(),
                    CopyEditorSystemMessage(),
                    DataSourceMessage.from_context(self.datasource),
                    InlineEditUserMessage.from_context(
                        user_prompt=self.user_prompt,
                        page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                        page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                        selected_text=self.selected_text,
                    ),
                ]
            ),
            tool_types=[HybridSearchTool],
            iterations=2,
            datasource=self.datasource,
        )
        return InlineEditPipelineResponse(
            final_response=information_response.content,
            references=list({ref for tool in called_tools for ref in tool.references}),
        )

    async def stream(
        self, client: LlmClient = LlmClient.o3_mini()
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        llm_session_id = uuid.uuid4()
        yield StartSessionStreamResponse(
            kind=LlmStreamResponseKind.START_SESSION,
            llm_session_id=llm_session_id,
        )
        abbreviated_page_content = abbreviate_page_content(
            user_prompt=self.user_prompt,
            page_content_before_cursor=self.page_content_before_cursor,
            page_content_after_cursor=self.page_content_after_cursor,
        )
        async for chunk in client.multi_shot_stream(
            message_history=LlmMessageHistory(
                messages=[
                    GlobalSystemMessage(),
                    SoftwareExpertiseMessage(),
                    InlineEditSystemMessage(),
                    InlineEditToolUseMessage(),
                    CopyEditorSystemMessage(),
                    DataSourceMessage.from_context(self.datasource),
                    InlineEditUserMessage.from_context(
                        user_prompt=self.user_prompt,
                        page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                        page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                        selected_text=self.selected_text,
                    ),
                ]
            ),
            tool_types=[HybridSearchTool],
            iterations=2,
            datasource=self.datasource,
        ):
            yield chunk
        yield EndSessionStreamResponse(
            kind=LlmStreamResponseKind.END_SESSION,
            llm_session_id=llm_session_id,
        )
