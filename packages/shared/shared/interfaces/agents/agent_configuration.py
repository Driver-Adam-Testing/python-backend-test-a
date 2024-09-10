from pydantic import BaseModel
from shared.agent import tools as agent_tools
from shared.interfaces.agents.data_scope import DataScope


class AgentConfiguration(BaseModel):
    """
    Configuration for an agent.

    Attributes:
        model (str | None): The model to be used by the agent.
        system_prompts (list[str] | None): List of system prompts.
        user_prompt (str | None): The user prompt.
        iterations (int): Number of iterations the agent should perform.
        tools (list[ToolConfig]): List of tools configurations.
    """

    model: str | None = None
    system_prompts: list[str] = []
    iterations: int = 1
    tool_names: list[str] = []
    scope: DataScope = DataScope(paths=[], organization_id=None)

    @property
    def tools(self) -> list[type]:
        """
        Retrieve the tool functions based on the tool configurations.

        Returns:
            list[Tool]: List of tool instances.

        Raises:
            TypeError: If the tool is not an instance of Tool.
            AttributeError: If the tool does not exist in agent_tools.
        """
        tools = []
        for tool_name in [t.name for t in self.tool_names]:
            if hasattr(agent_tools, tool_name):
                tool_class = getattr(agent_tools, tool_name)
                tools.append(tool_class)
        return tools

    def create_system_prompts(self) -> list[str]:
        """
        Create a list of system prompts in the required format.

        Args:
            system_prompts (list[str]): List of system prompts as strings.

        Returns:
            list[dict]: List of system prompts formatted as dictionaries.
        """
        from shared import prompts

        formatted_prompts = []
        if self.system_prompts:
            for system_prompt in self.system_prompts:
                module_name, attribute_name = system_prompt.rsplit(".", 1)
                try:
                    module = getattr(prompts, module_name)
                    formatted_prompts.append(getattr(module, attribute_name).MESSAGE)
                except AttributeError:
                    formatted_prompts.append(
                        {"role": "system", "content": system_prompt}
                    )
        return formatted_prompts
