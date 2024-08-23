from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.agent.tools import agent_tools
from shared.interfaces.agents.execute import AgentConfiguration, AgentResult, AgentScope


def run_agent_prompt_augmentation(
    prompt: str, agent_config: AgentConfiguration, scope: AgentScope
) -> AgentResult:
    agent = create_agent(
        model=agent_config.model,
        organization_id=scope.organization_id,
        max_iterations=3,
        tools=[agent_tools.search_tech_docs_tool],
        paths=scope.paths,
    )
    agent.add_message(prompts.interface.batch_tools.MESSAGE)
    agent.add_message(prompts.interface.technical_context_interface.MESSAGE)
    agent.add_message(prompts.voice.software_engineer.MESSAGE)
    agent.add_message(prompts.task.prompt_augmentation.MESSAGE)
    response = agent.invoke(prompt)

    return AgentResult(result=response, search_results=agent.search_results)
