from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.pipeline_configuration import (
    PipelineStepConfiguration,
    PipelineStepResponse,
)


def run_agent_copy_editor(input: PipelineStepConfiguration):
    agent = create_agent(
        model=input.model,
        organization_id=input.scope.organization_id,
        max_iterations=input.iterations,
        tools=input.tools,
        paths=input.scope.paths,
    )
    for system_prompt in input.create_system_prompts():
        agent.add_message(system_prompt)
    agent.add_message(prompts.voice.copy_editor.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_speculation.MESSAGE)
    agent.add_message(prompts.voice.copy_editor_remove_useless_language.MESSAGE)
    response = agent.invoke(str(input.prompt))
    return PipelineStepResponse(
        agent_id=agent.agent_id,
        search_results=agent.search_results,
        agent_result=response,
    )
