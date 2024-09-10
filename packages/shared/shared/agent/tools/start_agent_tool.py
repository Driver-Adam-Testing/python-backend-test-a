from shared.agent.tools.tool_strict import ToolStrict
from shared.interfaces.agents.data_scope import DataScope
from shared.interfaces.agents.pipeline_configuration import (
    AgentConfiguration,
    PipelineInput,
    PipelineStepResponse,
)


class StartAgentTool(ToolStrict):
    """
    StartAgentTool is a strict tool class designed to start an agent with a given configuration
    and execute a prompt.

    Attributes:
        agent_config (AgentConfiguration): The configuration for the agent to be started.
        prompt (str): The prompt to be executed by the agent.
    """

    agent_config: AgentConfiguration
    prompt: str

    def execute(self, agent):
        # Create the input for agent execution
        agent_input = PipelineInput(
            prompt=self.prompt,
            agent_config=self.agent_config,
            scope=DataScope(paths=agent.paths, organization_id=agent.organization_id),
        )
        from shared.pipelines.agents.execute import execute_single

        # Execute the agent
        response: PipelineStepResponse = execute_single(agent_input)

        # Return the result of the agent execution
        return response.result
