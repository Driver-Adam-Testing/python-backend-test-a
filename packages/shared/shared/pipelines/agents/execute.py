from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
    PipelineStepType,
)
from shared.interfaces.agents.prompt import PromptWithContext
from shared.pipelines.agents.agent_code_critic import (
    run_agent_code_critic__extract_verify_correct,
)
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)


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
    sequence_response = PipelineResponse(step_responses=[], final_result="")
    sequence_prompt = PromptWithContext(prompt=input.prompt, context=input.context)
    working_response = None
    sequence_prompt.add_to_context(
        {
            "searchable_paths_and_root_directories": "these paths must be the path or path-prefix of any searches: "
            + str(input.scope.paths)
        }
    )

    for step in input.steps:
        step.prompt = sequence_prompt
        step.scope = input.scope

        match step.step_type:
            case PipelineStepType.PROMPT_AUGMENTATION:
                response = run_agent_prompt_augmentation(step)
                sequence_prompt.add_to_context({"original_user_prompt": input.prompt})
                sequence_response.step_responses.append(response)
                sequence_prompt.prompt = response.agent_result
                continue

            case PipelineStepType.CODE_CRITIC:
                # Code critic expects the document as the prompt
                if working_response:
                    step.prompt.prompt = working_response
                response = run_agent_code_critic__extract_verify_correct(step)
                sequence_response.step_responses.append(response)
                working_response = response.agent_result[-1]
                continue

            case PipelineStepType.COPY_EDITOR:
                # Copy Editor expects the document as the prompt
                if working_response:
                    step.prompt.prompt = working_response
                response = run_agent_copy_editor(step)

            case PipelineStepType.DEFAULT:
                # Default Agent makes no assumptions, it could be in the middle of a sequence or not. Assume the prompt, plus the working document of the sequence
                if working_response:
                    step.prompt.prompt = f"Enhance the working document:\n<document>\n{working_response}\n</document>\nAccording to the instructions\n{sequence_prompt.prompt}"
                response = run_agent_default(step)

        working_response = response.agent_result
        sequence_response.step_responses.append(response)

    sequence_response.final_result = sequence_response.step_responses[-1].agent_result
    return sequence_response
