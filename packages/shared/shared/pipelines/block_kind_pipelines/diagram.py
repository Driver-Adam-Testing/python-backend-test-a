from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
    PipelineStepConfiguration,
    PipelineStepType,
)
from shared.interfaces.agents.prompt import PromptWithContext
from shared.interfaces.usage.event_metadata import UsageSessionMetadata
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)
from shared.prompts.block_kind.block_kind_diagram import BlockKindCopyEditorDiagram
from shared.usage.llm_session import LLMUsageSession

PROMPT_AUG_PROMPT_SUFFIX = (
    """Generate a comprehensive mermaid diagram as its desired output."""
)


def execute_diagram_block_agent(input: PipelineInput) -> PipelineResponse:
    session_meta = UsageSessionMetadata(
        content_type="page",
        content_id="Add document id here",
    )
    with LLMUsageSession(
        input.scope.organization_id, input.scope.user_id, session_meta
    ) as llm_usage_session:
        prompt_augmentation_input = PipelineStepConfiguration(
            step_type=PipelineStepType.PROMPT_AUGMENTATION,
            prompt=PromptWithContext(
                prompt=input.prompt + PROMPT_AUG_PROMPT_SUFFIX, context=input.context
            ),
            scope=input.scope,
            iterations=1,  # Specify the number of iterations if needed
        )
        response = run_agent_prompt_augmentation(
            prompt_augmentation_input, llm_usage_session
        )
    default_agent_input = PipelineStepConfiguration(
        step_type=PipelineStepType.SMART_INSTRUCTION,
        prompt=PromptWithContext(
            prompt=prompt_augmentation_input.prompt.prompt,
            context=prompt_augmentation_input.prompt.context,
        ),
        scope=input.scope,
        iterations=4,
        tool_names=[
            "SearchTool",
            "OpenFileTool",
            "CodebaseFolderSummaryTool",
        ],
        system_prompts=[
            "voice.software_engineer",
            "interface.technical_context_interface",
            "task.selected_text",
            "voice.copy_editor",
        ],
        response_format=BlockKindCopyEditorDiagram,
    )

    default_response = run_agent_default(default_agent_input, llm_usage_session)
    if isinstance(default_response, BlockKindCopyEditorDiagram):
        final_result = default_response.agent_result.to_markdown()

    response = PipelineResponse(
        step_responses=[response, default_response],
        final_result=final_result,
    )
    return response
