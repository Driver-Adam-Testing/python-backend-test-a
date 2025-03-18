from pydantic import BaseModel
from shared.interfaces.agents.block_kind import BlockKind
from shared.v3 import DataSource, LlmClient, LlmMessageHistory, Reference
from shared.v3.app.pipelines.abbreviate_page_content import (
    abbreviate_page_content,
)
from shared.v3.app.static.messages.copy_editor_messages import (
    CopyEditorSystemMessage,
    CopyEditorUserMessage,
)
from shared.v3.app.static.messages.smart_instruction_input_message import (
    SmartInstructionInputMessage,
)
from shared.v3.app.static.messages.software_expertise import SoftwareExpertiseMessage
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool


class SmartInstructionPipelineResponse(BaseModel):
    final_response: str
    references: list[Reference]


def run_smart_instruction(
    user_prompt: str,
    text_before_instruction: str,
    text_after_instruction: str,
    datasource: DataSource,
    block_kind: BlockKind = BlockKind.ANY,
    client: LlmClient = LlmClient.gpt_4o_mini(),
) -> SmartInstructionPipelineResponse:
    abbreviated_page_content = abbreviate_page_content(
        user_prompt=user_prompt,
        page_content_before_cursor=text_before_instruction,
        page_content_after_cursor=text_after_instruction,
    )
    # TODO: pre-search and give all Datascoure top level information to the LLM
    # TODO: Break long context windows up automatically in a multi-shot situation
    information_response, called_tools, _ = client.multi_shot(
        message_history=LlmMessageHistory(
            messages=[
                SoftwareExpertiseMessage(),
                SmartInstructionInputMessage.from_context(
                    prompt=user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                ),
            ]
        ),
        tool_types=[HybridSearchTool],
        iterations=3,
        datasource=datasource,
    )
    copy_editor_response = client.single_shot(
        message_history=LlmMessageHistory(
            messages=[
                SoftwareExpertiseMessage(),
                CopyEditorSystemMessage(),
                CopyEditorUserMessage.from_context(
                    text_to_edit=information_response.content,
                    original_user_prompt=user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                ),
            ]
        ),
    )

    return SmartInstructionPipelineResponse(
        final_response=copy_editor_response.content,
        references=list(set({ref for tool in called_tools for ref in tool.references})),
    )
