from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.agent.tools.open_file_tool import OpenFileTool
from shared.agent.tools.search_tool import SearchTool
from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
    PipelineStepConfiguration,
    PipelineStepResponse,
)
from shared.interfaces.agents.prompt import PromptWithContext
from shared.interfaces.usage.event_metadata import UsageSessionMetadata
from shared.pipelines.agents.agent_code_critic import (
    run_agent_code_critic__extract_verify_correct,
)
from shared.prompts.block_kind.block_kind_code import BlockKindCopyEditorCodeBlock
from shared.usage.llm_session import LLMUsageSession

PROMPT_AUG_PROMPT_SUFFIX = (
    """Generate comprehensive code snippets as the desired output."""
)


def execute_code_block_agent(input: PipelineInput) -> PipelineResponse:
    session_meta = UsageSessionMetadata(
        content_type="page",
        content_id="Add document id here",
    )
    with LLMUsageSession(
        input.scope.organization_id, input.scope.user_id, session_meta
    ) as llm_usage_session:
        agent = create_agent(
            scope=input.scope,
            model=None,
            max_iterations=4,
            tools=[SearchTool, OpenFileTool],
            llm_usage_session=llm_usage_session,
            response_type=BlockKindCopyEditorCodeBlock,
        )
        agent.add_message(prompts.voice.software_engineer.MESSAGE)
        agent.add_message(prompts.interface.technical_context_interface.MESSAGE)
        agent.add_message(prompts.voice.copy_editor.MESSAGE)
        agent.add_message(prompts.voice.software_engineer.MESSAGE)
        response = agent.invoke(str(input.prompt))
        code_corrections_response = run_agent_code_critic__extract_verify_correct(
            PipelineStepConfiguration(
                prompt=PromptWithContext(prompt=response.to_markdown()),
                scope=input.scope,
            ),
            llm_usage_session,
        )
        code_corrections = code_corrections_response.agent_result
        final_result = response.to_markdown()
        if isinstance(code_corrections, list):
            for correction in code_corrections:
                if (
                    hasattr(correction.agent_result, "corrected")
                    and correction.agent_result.corrected
                ):
                    final_result = final_result.replace(
                        correction.agent_result.input_code,
                        correction.agent_result.corrected_code,
                    )

    response = PipelineResponse(
        step_responses=[
            PipelineStepResponse(
                agent_id=agent.agent_id,
                agent_result=response,
                search_results=agent.search_results,
            ),
            code_corrections_response,
        ],
        final_result=final_result,
    )
    return response
