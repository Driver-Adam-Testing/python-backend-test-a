from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.execute import AgentConfiguration, AgentResult, AgentScope


def run_agent_default(prompt: str, agent_config: AgentConfiguration, scope: AgentScope):
    agent = create_agent(
        model=agent_config.model,
        organization_id=scope.organization_id,
        max_iterations=agent_config.iterations,
        tools=agent_config.get_tool_functions(),
        paths=scope.paths,
    )
    if agent_config.system_prompts:
        for system_prompt in agent_config.system_prompts:
            module_name, attribute_name = system_prompt.rsplit(".", 1)
            module = getattr(prompts, module_name)
            agent.add_message(getattr(module, attribute_name).MESSAGE)
    response = agent.invoke(prompt)
    return AgentResult(result=response, search_results=agent.search_results)
