from collections.abc import AsyncGenerator

from shared.v3 import LlmClient, LlmMessage, LlmMessageHistory, MessageKind
from shared.v3.app.pipelines.abbreviate_page_content import abbreviate_page_content
from shared.v3.app.pipelines.pipeline_request import PipelineRequest
from shared.v3.app.pipelines.pipeline_response import PipelineResponse
from shared.v3.app.static.messages.copy_editor_messages import CopyEditorSystemMessage
from shared.v3.app.static.messages.driver_app_messages import PromptGuidelinesMessage
from shared.v3.app.static.messages.format_kind_message import FormatKindMessage
from shared.v3.app.static.messages.smart_instruction_messages import (
    SmartInstructionInputMessage,
)
from shared.v3.app.static.messages.software_expertise import SoftwareExpertiseMessage
from shared.v3.app.static.tools.folder_summary import FolderSummaryTool
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.app.static.tools.open_file import OpenFileTool
from shared.v3.globals.datasource_messages import DataSourceMessage
from shared.v3.globals.global_messages import GlobalSystemMessage
from shared.v3.interfaces.llm_stream_response import (
    LlmStreamResponse,
)


class SmartInstructionPipelineResponse(PipelineResponse):
    pass


class SmartInstructionPipelineRequest(PipelineRequest):
    user_prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    format_kind: str

    def _run(
        self, client: LlmClient = LlmClient.gpt_4_1()
    ) -> SmartInstructionPipelineResponse:
        abbreviated_page_content = abbreviate_page_content(
            user_prompt=self.user_prompt,
            page_content_before_cursor=self.page_content_before_cursor,
            page_content_after_cursor=self.page_content_after_cursor,
        )
        message_history = LlmMessageHistory(
            messages=[
                GlobalSystemMessage(),
                SoftwareExpertiseMessage(),
                PromptGuidelinesMessage(),
                DataSourceMessage.from_context(self.datasource),
                FormatKindMessage.from_context(self.format_kind),
                SmartInstructionInputMessage.from_context(
                    prompt=self.user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                ),
            ]
        )
        response, called_tools = client.multi_shot(
            message_history=message_history,
            tool_types=[HybridSearchTool, OpenFileTool, FolderSummaryTool],
            iterations=3,
            datasource=self.datasource,
        )
        message_history.add_message(CopyEditorSystemMessage())
        message_history.add_message(
            LlmMessage(
                message_kind=MessageKind.USER, content="Copy Edit the last response"
            )
        )
        response, called_tools = client.multi_shot(
            message_history=message_history,
            tool_types=[],
            iterations=1,
            datasource=self.datasource,
        )
        return SmartInstructionPipelineResponse(
            final_response=response.content,
            references=list({ref for tool in called_tools for ref in tool.references}),
        )

    async def _stream(
        self, client: LlmClient = LlmClient.gpt_4_1()
    ) -> AsyncGenerator[LlmStreamResponse, None]:
        abbreviated_page_content = abbreviate_page_content(
            user_prompt=self.user_prompt,
            page_content_before_cursor=self.page_content_before_cursor,
            page_content_after_cursor=self.page_content_after_cursor,
        )
        message_history = LlmMessageHistory(
            messages=[
                GlobalSystemMessage(),
                SoftwareExpertiseMessage(),
                PromptGuidelinesMessage(),
                DataSourceMessage.from_context(self.datasource),
                FormatKindMessage.from_context(self.format_kind),
                SmartInstructionInputMessage.from_context(
                    prompt=self.user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                ),
            ]
        )
        async for response in client.multi_shot_stream(
            message_history=message_history,
            tool_types=[HybridSearchTool, OpenFileTool, FolderSummaryTool],
            iterations=3,
            datasource=self.datasource,
        ):
            yield response
        message_history.add_message(CopyEditorSystemMessage())
        message_history.add_message(
            LlmMessage(
                message_kind=MessageKind.USER, content="Copy Edit the last response"
            )
        )
        async for response in client.multi_shot_stream(
            message_history=message_history,
            tool_types=[],
            iterations=1,
            datasource=self.datasource,
        ):
            yield response
