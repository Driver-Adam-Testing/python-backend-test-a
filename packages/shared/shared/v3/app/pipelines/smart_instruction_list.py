from shared.interfaces.agents.data_scope import DataScope
from shared.v3.app.pipelines.abbreviate_page_content import (
    AbbreviatedPageContentPipelineResponse,
    abbreviate_page_content,
)
from shared.v3.app.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.app.static.messages.smart_instruction_input_message import (
    SmartInstructionInputMessage,
)
from shared.v3.app.static.response_types.response_type_list import (
    ListResponse,
)
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient


def run_smart_instruction_list(
    user_prompt: str,
    text_before_instruction: str,
    text_after_instruction: str,
    datascope: DataScope,
    client: LlmClient = LlmClient.gpt_4o_mini(),
) -> dict:
    abbreviated_page_content: AbbreviatedPageContentPipelineResponse = (
        abbreviate_page_content(
            pipeline_execution_request=PipelineExecutionRequest(
                original_prompt=user_prompt,
                text_before_selection=text_before_instruction,
                text_after_selection=text_after_instruction,
                selected_text=None,
                datascope=datascope,
            )
        )
    )
    response, _, called_tools = client.multi_shot(
        iterations=3,
        response_type=ListResponse,
        tool_types=[HybridSearchTool],
        message_history=LlmMessageHistory(
            messages=[
                SmartInstructionInputMessage.from_context(
                    prompt=user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                )
            ]
        ),
        datascope=datascope,
    )
    return {
        "final_response": response.parsed_content.to_markdown(),
        "references": list(
            set({ref for tool in called_tools for ref in tool.references})
        ),
    }
