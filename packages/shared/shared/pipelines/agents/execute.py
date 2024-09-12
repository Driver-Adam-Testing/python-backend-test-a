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


def execute_sequence(input: PipelineInput):
    sequence_response = PipelineResponse(step_responses=[], final_result="")
    current_prompt = PromptWithContext(prompt=input.prompt, context=input.context)
    if any(
        step.step_type == PipelineStepType.PROMPT_AUGMENTATION
        for step in input.steps[1:]
    ):
        raise ValueError(
            "Prompt augmentation steps are only allowed as the first step in the sequence."
        )

    for _, step in enumerate(input.steps):
        if step.scope.organization_id is None:
            step.scope = input.scope
        if step.prompt is None:
            step.prompt = current_prompt

        match step.step_type:
            case PipelineStepType.PROMPT_AUGMENTATION:
                response = run_agent_prompt_augmentation(step)
                current_prompt = PromptWithContext(
                    prompt=response.agent_result, context=input.context
                )

            case PipelineStepType.DEFAULT:
                response = run_agent_default(step)

            case PipelineStepType.COPY_EDITOR:
                response = run_agent_copy_editor(step)

            case PipelineStepType.CODE_CRITIC:
                response = run_agent_code_critic__extract_verify_correct(step)
                sequence_response.step_responses.append(response)
                current_prompt = PromptWithContext(
                    prompt=response.agent_result[-1], context=input.context
                )
                sequence_response.final_result = response.agent_result[-1]
                continue
        # if step.step_type == PipelineStepType.EDIT_DOCUMENT:
        #     return run_agent_edit_document(input)
        sequence_response.step_responses.append(response)
        sequence_response.final_result = response
        current_prompt = PromptWithContext(
            prompt=response.agent_result, context=input.context
        )

    return sequence_response
