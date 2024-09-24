from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.pipeline_configuration import (
    PipelineStepConfiguration,
    PipelineStepResponse,
)


def run_agent_default(input: PipelineStepConfiguration):
    agent = create_agent(
        scope=input.scope,
        model=input.model,
        max_iterations=input.iterations,
        tools=input.tools,
    )
    for system_prompt in input.create_system_prompts():
        agent.add_message(system_prompt)
    agent.add_message(prompts.voice.software_engineer.MESSAGE)

    response = agent.invoke(str(input.prompt))
    return PipelineStepResponse(
        agent_id=agent.agent_id,
        agent_result=response,
        search_results=agent.search_results,
    )
