from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.execute import AgentExecuteInput, AgentExecutionResponse


def run_agent_default(input: AgentExecuteInput):
    agent = create_agent(
        model=input.agent_config.model,
        organization_id=input.scope.organization_id,
        max_iterations=input.agent_config.iterations,
        tools=input.agent_config.get_tool_functions(),
        paths=input.scope.paths,
    )
    for system_prompt in input.agent_config.create_system_prompts():
        agent.add_message(system_prompt)
    response = agent.invoke(input.create_user_prompt())
    print("SEARCH RESULTS: " + str(len(agent.search_results)))
    return AgentExecutionResponse(
        agent_id=agent.agent_id,
        agent_result=response,
        search_results=agent.search_results,
    )
