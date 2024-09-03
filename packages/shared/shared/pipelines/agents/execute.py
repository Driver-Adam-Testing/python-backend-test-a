from shared.interfaces.agents.execute import (
    AgentExecuteInput,
    AgentExecutionResponse,
    AgentExecutionSequenceResponse,
    AgentType,
)
from shared.pipelines.agents.agent_code_critic import run_agent_code_critic
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_edit_document import (
    AgentEditDocumentExecuteInput,
    run_agent_edit_document,
)
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)


def execute_sequence(input: AgentExecuteInput):
    context = {}
    response = AgentExecutionSequenceResponse(responses=[])

    for agent_config in input.agent_config:
        prompt = input.create_user_prompt()
        if len(response.responses) > 0:
            prompt = response.responses[-1].agent_result
        if agent_config.user_prompt:
            prompt = agent_config.user_prompt

        single_input = AgentExecuteInput(
            prompt=prompt,
            agent_config=agent_config,
            scope=input.scope,
            context=context,
        )
        single_response = execute_single(single_input)
        response.responses.append(single_response)

    return response


def execute_single(
    input: AgentExecuteInput | AgentEditDocumentExecuteInput,
) -> AgentExecutionResponse:
    if input.agent_config.agent_type == AgentType.DEFAULT:
        return run_agent_default(input)
    if input.agent_config.agent_type == AgentType.PROMPT_AUGMENTATION:
        return run_agent_prompt_augmentation(input)
    if input.agent_config.agent_type == AgentType.COPY_EDITOR:
        return run_agent_copy_editor(input)
    if input.agent_config.agent_type == AgentType.CODE_CRITIC:
        return run_agent_code_critic(input)
    if input.agent_config.agent_type == AgentType.EDIT_DOCUMENT:
        return run_agent_edit_document(input)
    raise ValueError(f"Unknown agent type: {input.agent_config.agent_type}")
