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
    LlmStreamResponse,
)


class InlineEditPipelineResponse(PipelineResponse):
    pass


class InlineEditPipelineRequest(PipelineRequest):
    user_prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    cursor_selection: str

    def _run(
        self, client: LlmClient = LlmClient.gpt_4_1()
    ) -> InlineEditPipelineResponse:
        # TODO: can I make the meat of this one method?
        abbreviated_page_content = abbreviate_page_content(
            user_prompt=self.user_prompt,
            page_content_before_cursor=self.page_content_before_cursor,
            page_content_after_cursor=self.page_content_after_cursor,
        )
        # TODO: how do I handle the multiple histories? Should I save abbreviation?
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
                        selected_text=self.cursor_selection,
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

    async def _stream(
        self, client: LlmClient = LlmClient.o3_mini()
    ) -> AsyncGenerator[LlmStreamResponse, None]:
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
                        selected_text=self.cursor_selection,
                    ),
                ],
                llm_session_id=self.llm_session.id,
            ),
            tool_types=[HybridSearchTool],
            iterations=2,
            datasource=self.datasource,
        ):
            yield chunk
