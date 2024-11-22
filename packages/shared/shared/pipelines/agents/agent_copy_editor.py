from shared import prompts
from shared.agent.agent_factory import create_agent
from shared.interfaces.agents.pipeline_configuration import (
    PipelineStepConfiguration,
    PipelineStepResponse,
)


def run_agent_copy_editor(input: PipelineStepConfiguration) -> PipelineStepResponse:
    agent = create_agent(
        scope=input.scope,
        model=input.model,
        max_iterations=input.iterations,
        tools=input.tools,
    )
    for system_prompt in input.create_system_prompts():
        agent.add_message(system_prompt)
    # TODO: Make this a branch based on a parsed LLM response, rather than a string comparison.
    # The next version of pipelines should consider branching logic based on response_formats.
    if "```mermaid" in str(input.prompt) or "diagram" in str(input.prompt).lower():
        agent.add_message(prompts.task.codeblock_syntax_mermaid.MESSAGE)
    agent.add_message(prompts.voice.copy_editor.MESSAGE)
    response = agent.invoke(str(input.prompt))

    return PipelineStepResponse(
        agent_id=agent.agent_id,
        search_results=agent.search_results,
        agent_result=response,
    )
