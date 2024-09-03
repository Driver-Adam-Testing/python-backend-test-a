from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.execute import (
    AgentExecuteInput,
    AgentExecutionResponse,
)


def run_agent_copy_editor(input: AgentExecuteInput):
    agent = create_agent(
        model=input.agent_config.model,
        organization_id=input.scope.organization_id,
        max_iterations=input.agent_config.iterations,
        tools=input.agent_config.get_tool_functions(),
        paths=input.scope.paths,
    )
    for system_prompt in input.agent_config.create_system_prompts():
        agent.add_message(system_prompt)
    agent.add_message(prompts.voice.copy_editor.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_speculation.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_useless_language.MESSAGE)
    response = agent.invoke(input.prompt)
    return AgentExecutionResponse(
        agent_id=agent.agent_id,
        search_results=agent.search_results,
        agent_result=response,
    )
