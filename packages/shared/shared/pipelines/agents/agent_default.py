from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.pipeline_configuration import (
    PipelineStepConfiguration,
    PipelineStepResponse,
)
from shared.usage.llm_session import LLMUsageSession


def run_agent_default(
    input: PipelineStepConfiguration, llm_usage_session: LLMUsageSession
) -> PipelineStepResponse:
    agent = create_agent(
        scope=input.scope,
        model=input.model,
        max_iterations=input.iterations,
        tools=input.tools,
        llm_usage_session=llm_usage_session,
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
