from shared.interfaces.agents.execute import (
    AgentExecuteInput,
    AgentExecuteSequenceInput,
    AgentExecutionResponse,
    AgentType,
)
from shared.pipelines.agents.agent_copy_editor import run_agent_copy_editor
from shared.pipelines.agents.agent_default import run_agent_default
from shared.pipelines.agents.agent_prompt_augmentation import (
    run_agent_prompt_augmentation,
)


def execute_sequence(input: AgentExecuteSequenceInput):
    agent_results = []
    output = input.prompt
    context = []

    for agent_config in input.agent_configs:
        context.append(output)
        single_input = AgentExecuteInput(
            prompt=agent_config.user_prompt if agent_config.user_prompt else output,
            agent_config=agent_config,
            scope=input.scope,
            context=context,
        )
        single_response = execute_single(single_input)
        output = single_response.result
        agent_results.append(single_response.agent_results[0])

    return AgentExecutionResponse(
        result=agent_results[-1].result, agent_results=agent_results
    )


def execute_single(input: AgentExecuteInput):
    output = input.prompt

    if input.agent_config.agent_type == AgentType.DEFAULT:
        output = run_agent_default(
            prompt=input.create_user_prompt(),
            agent_config=input.agent_config,
            scope=input.scope,
        )
    if input.agent_config.agent_type == AgentType.PROMPT_AUGMENTATION:
        output = run_agent_prompt_augmentation(
            prompt=input.prompt,
            agent_config=input.agent_config,
            scope=input.scope,
        )
    if input.agent_config.agent_type == AgentType.COPY_EDITOR:
        output = run_agent_copy_editor(
            prompt=input.create_user_prompt(),
            agent_config=input.agent_config,
            scope=input.scope,
        )
    return AgentExecutionResponse(result=output.result, agent_results=[output])
