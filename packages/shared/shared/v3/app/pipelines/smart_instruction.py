from shared.interfaces.agents.data_scope import DataScope
from shared.v3.app.pipelines.abbreviate_page_content import (
    AbbreviatedPageContentPipelineResponse,
    abbreviate_page_content,
)
from shared.v3.app.pipelines.interfaces.pipeline_request import PipelineExecutionRequest
from shared.v3.app.static.messages.smart_instruction_input_message import (
    SmartInstructionInputMessage,
)
from shared.v3.app.static.tools.hybrid_search import HybridSearchTool
from shared.v3.interfaces.llm_message_history import LlmMessageHistory
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.llms.clients.multishot_llm_client import MultiShotLlmClient


def run_smart_instruction(
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
    agent = MultiShotLlmClient(
        datascope=datascope,
        config=client.config,
        tools=[HybridSearchTool],
        message_history=LlmMessageHistory(
            messages=[
                SmartInstructionInputMessage.from_context(
                    prompt=user_prompt,
                    page_content_before_cursor=abbreviated_page_content.abbreviated_before,
                    page_content_after_cursor=abbreviated_page_content.abbreviated_after,
                )
            ]
        ),
    )
    response = agent.invoke(iterations=3)

    return {
        "abbreviated_before": abbreviated_page_content.abbreviated_before
        if abbreviated_page_content.abbreviated_before
        else "",
        "abbreviated_after": abbreviated_page_content.abbreviated_after
        if abbreviated_page_content.abbreviated_after
        else "",
        "final_response": response.content,
        "references": list(
            set({ref for tool in agent.called_tools for ref in tool.references})
        ),
    }
