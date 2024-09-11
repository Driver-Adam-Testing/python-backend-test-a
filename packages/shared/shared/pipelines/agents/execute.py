from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
    PipelineStepType,
)
from shared.interfaces.agents.prompt import PromptWithContext
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)


def execute_sequence(input: PipelineInput):
    sequence_response = PipelineResponse(step_responses=[])
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

        if step.step_type == PipelineStepType.PROMPT_AUGMENTATION:
            response = run_agent_prompt_augmentation(step)
            current_prompt = PromptWithContext(
                prompt=response.agent_result, context=input.context
            )

        if step.step_type == PipelineStepType.DEFAULT:
            response = run_agent_default(step)

        if step.step_type == PipelineStepType.COPY_EDITOR:
            response = run_agent_copy_editor(step)
        # if step.step_type == PipelineStepType.CODE_CRITIC:
        #     return run_agent_code_critic(input)
        # if step.step_type == PipelineStepType.EDIT_DOCUMENT:
        #     return run_agent_edit_document(input)
        sequence_response.step_responses.append(response)
        current_prompt = PromptWithContext(
            prompt=response.agent_result, context=input.context
        )

    return sequence_response
