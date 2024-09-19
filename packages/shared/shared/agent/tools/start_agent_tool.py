## TODO: THIS IS CAUSING A CIRCULAR IMPORT, WILL ADDRESS SOON

# from shared.agent.tools.tool_strict import ToolStrict
# from shared.interfaces.agents.data_scope import DataScope
# from shared.interfaces.agents.pipeline_configuration import (
#     PipelineInput,
#     PipelineResponse,
#     PipelineStepConfiguration,
#     PipelineStepType,
# )
# import enum
# from shared.pipelines.agents.agent_default import run_agent_default

# class StartAgentToolNames(str, enum.Enum):
#     SearchTool = "SearchTool"
#     OpenFileTool = "OpenFileTool"


# class StartAgentTool(ToolStrict):
#     """
#     StartAgentTool is a strict tool class designed to start an agent with a given configuration
#     and execute a prompt.

#     Attributes:
#         system_prompts (list[str]): List of system prompts.
#         iterations (int): Number of iterations the agent should perform.
#         tool_names (list[str]): List of tool names to be used by the agent.
#         root_data_access_paths (list[str]): List of root data access paths.
#         prompt (str): The prompt to be executed by the agent.
#     """

#     system_prompts: list[str] = []
#     iterations: int = 2
#     tool_names: list[StartAgentToolNames] = []
#     root_data_search_paths: list[str]
#     prompt: str

#     def execute(self, agent):
#         # Create the input for agent execution
#         agent_input = PipelineInput(
#             prompt=self.prompt,
#             context=None,  # Assuming context is an empty list, adjust as needed
#             scope=DataScope(paths=self.root_data_search_paths, organization_id=agent.organization_id),
#             steps=[
#                 PipelineStepConfiguration(
#                     model=None,
#                     system_prompts=self.system_prompts,
#                     iterations=self.iterations,
#                     tool_names=[tool_name.value for tool_name in self.tool_names],
#                     scope=DataScope(paths=self.root_data_search_paths, organization_id=agent.organization_id),
#                     step_type=PipelineStepType.DEFAULT,
#                 )
#             ],
#         )

#         # Execute the agent pipeline using run_agent_default
#         response: PipelineResponse = run_agent_default(agent_input)

#         # Return the final result of the agent execution
#         return response.final_result
