from pydantic import BaseModel
from shared.v3 import DataSource, LlmClient, LlmMessageHistory, Reference
from shared.v3.app.pipelines.abbreviate_page_content import (
    abbreviate_page_content,
)
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


class InlineEditPipelineResponse(BaseModel):
    final_response: str
    references: list[Reference]


def run_inline_edit(
    user_prompt: str,
    text_before_instruction: str,
    text_after_instruction: str,
    datasource: DataSource,
    selected_text: str,
    client: LlmClient = LlmClient.o3_mini(),
) -> InlineEditPipelineResponse:
    abbreviated_page_content = abbreviate_page_content(
        user_prompt=user_prompt,
        page_content_before_cursor=text_before_instruction,
        page_content_after_cursor=text_after_instruction,
    )
    information_response, called_tools = client.multi_shot(
        message_history=LlmMessageHistory(
            messages=[
                SoftwareExpertiseMessage(),
                InlineEditSystemMessage(),
                InlineEditToolUseMessage(),
                CopyEditorSystemMessage(),
                DataSourceMessage.from_context(datasource),
                InlineEditUserMessage.from_context(
                    user_prompt=user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                    selected_text=selected_text,
                ),
            ]
        ),
        tool_types=[HybridSearchTool],
        iterations=2,
        datasource=datasource,
    )

    return InlineEditPipelineResponse(
        final_response=information_response.content,
        references=list(set({ref for tool in called_tools for ref in tool.references})),
    )
