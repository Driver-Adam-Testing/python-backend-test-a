from shared.agent.agent_factory import create_agent
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
from shared.prompts.task.codeblock_syntax_mermaid import (
    PROMPT as CODEBLOCK_SYNTAX_MERMAID_PROMPT,
)
from shared.usage.llm_session import LLMUsageSession
from shared.utils.mermaid_render import is_mermaid_renderable

PROMPT_AUG_PROMPT_SUFFIX = (
    """Generate a comprehensive mermaid diagram as its desired output."""
)
DEFAULT_PROMPT_SUFFIX = f"""
    IMPORTANT: Ensure that diagram_mermaid is ONLY a single, code fenced, mermaid block.
    {CODEBLOCK_SYNTAX_MERMAID_PROMPT}
"""


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
        step_type=PipelineStepType.DEFAULT,
        prompt=PromptWithContext(
            prompt=DEFAULT_PROMPT_SUFFIX
            + "\n\n"
            + prompt_augmentation_input.prompt.prompt,
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
            "voice.copy_editor",
            "task.codeblock_syntax_mermaid",
        ],
        response_format=BlockKindCopyEditorDiagram,
    )

    default_response = run_agent_default(default_agent_input, llm_usage_session)
    mermaid_str = default_response.agent_result.to_mermaid_interior_string()
    attempts = 0
    max_attempts = 3
    is_renderable, error_message = is_mermaid_renderable(mermaid_str)
    while not is_renderable and attempts < max_attempts:
        agent = create_agent(
            scope=input.scope,
        )
        mermaid_str = agent.invoke(
            prompt=f"""
            The following is a mermaid diagram that is not renderable.
            Please fix the diagram.
            {error_message}
            {CODEBLOCK_SYNTAX_MERMAID_PROMPT}

            {mermaid_str}
            """,
            response_format=BlockKindCopyEditorDiagram,
        ).to_mermaid_interior_string()
        is_renderable, error_message = is_mermaid_renderable(mermaid_str)
        attempts += 1
    response = PipelineResponse(
        step_responses=[response, default_response],
        final_result=f"```mermaid\n{mermaid_str}```",
    )
    return response
