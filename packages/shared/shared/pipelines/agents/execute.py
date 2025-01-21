from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
    PipelineStepResponse,
    PipelineStepType,
)
from shared.interfaces.agents.prompt import PromptWithContext
from shared.interfaces.usage.event_metadata import UsageSessionMetadata
from shared.pipelines.agents.agent_code_critic import (
    run_agent_code_critic__extract_verify_correct,
)
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)
from shared.usage.llm_session import LLMUsageSession


def validate_pipeline(input: PipelineInput) -> None:
    # Prompt augmentation must be the first step or not present.
    if any(
        step.step_type == PipelineStepType.PROMPT_AUGMENTATION
        for step in input.steps[1:]
    ):
        raise ValueError(
            "Prompt augmentation steps are only allowed as the first step in the sequence."
        )

    # No using agents without an organization_id
    if not input.scope.organization_id:
        raise PermissionError("Authorization Error: Organization Id cannot be None")


def execute_sequence(input: PipelineInput) -> PipelineResponse:
    validate_pipeline(input)
    print(input)
    sequence_response = PipelineResponse(step_responses=[], final_result="")
    sequence_prompt = PromptWithContext(prompt=input.prompt, context=input.context)
    working_response = None
    if input.scope:
        paths_str = ", ".join(n.get_identifier() for n in input.scope.nodes)
        sequence_prompt.add_to_context(
            {
                "searchable_paths_and_directories_with_version_prefix": f"These paths and their children can be the path or path-prefix of any searches: \n\n{paths_str}"
            }
        )

    methods = {
        PipelineStepType.PROMPT_AUGMENTATION: run_agent_prompt_augmentation,
        PipelineStepType.CODE_CRITIC: run_agent_code_critic__extract_verify_correct,
        PipelineStepType.COPY_EDITOR: run_agent_copy_editor,
        PipelineStepType.DEFAULT: run_agent_default,
        PipelineStepType.SMART_INSTRUCTION: run_agent_default,
        PipelineStepType.EDIT_DOCUMENT: run_agent_default,
    }
    session_meta = UsageSessionMetadata(
        content_type="page",
        content_id="Add document id here",
    )
    with LLMUsageSession(
        input.scope.organization_id, input.scope.user_id, session_meta
    ) as llm_usage_session:
        for step in input.steps:
            response: PipelineStepResponse = methods[step.step_type](
                step.into_pipeline_step(
                    sequence_prompt=sequence_prompt,
                    input_scope=input.scope,
                    working_response=working_response,
                ),
                llm_usage_session,
            )
            sequence_response.step_responses.append(response)
            if step.step_type == PipelineStepType.PROMPT_AUGMENTATION:
                sequence_prompt.add_to_context({"original_user_prompt": input.prompt})
                sequence_prompt.prompt = response.agent_result
            elif step.step_type == PipelineStepType.COPY_EDITOR:
                working_response = response.agent_result[-1]
            else:
                working_response = response.agent_result
    sequence_response.final_result = sequence_response.step_responses[-1].agent_result
    return sequence_response
