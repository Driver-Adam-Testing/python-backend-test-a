import enum

from pydantic import BaseModel
from shared.agent import tools as agent_tools
from shared.interfaces.search import SearchResults


class AgentType(str, enum.Enum):
    """
    Enum representing different types of agents.
    """

    DEFAULT = "default"
    PROMPT_AUGMENTATION = "prompt_augmentation"
    COPY_EDITOR = "copy_editor"
    CODE_CRITIC = "code_critic"
    SMART_INSTRUCTION = "smart_instruction"


class ToolConfig(BaseModel):
    """
    Configuration for a tool used by an agent.

    Attributes:
        name (str): The name of the tool.
    """

    name: str


class AgentConfiguration(BaseModel):
    """
    Configuration for an agent.

    Attributes:
        model (str | None): The model to be used by the agent.
        system_prompts (list[str] | None): List of system prompts.
        user_prompt (str | None): The user prompt.
        agent_type (AgentType): The type of the agent.
        iterations (int): Number of iterations the agent should perform.
        tools (list[ToolConfig]): List of tools configurations.
    """

    model: str | None = None
    system_prompts: list[str] | None = None
    user_prompt: str | None = None
    agent_type: AgentType = AgentType.DEFAULT
    iterations: int = 1
    tools: list[ToolConfig] = []

    def get_tool_functions(self) -> list[agent_tools.ToolStrict]:
        """
        Retrieve the tool functions based on the tool configurations.

        Returns:
            list[Tool]: List of tool instances.

        Raises:
            TypeError: If the tool is not an instance of Tool.
            AttributeError: If the tool does not exist in agent_tools.
        """
        tools = []
        for tool_name in [t.name for t in self.tools]:
            if hasattr(agent_tools, tool_name):
                tool_class = getattr(agent_tools, tool_name)
                tools.append(tool_class)
        return tools


class UserPromptWithContext(BaseModel):
    """
    User prompt with additional context.

    Attributes:
        prompt (str): The user prompt.
        context (dict): Dictionary containing context information.
    """

    prompt: str
    context: dict

    def create_user_prompt(self):
        """
        Create a user prompt with context in XML format.

        Returns:
            str: The user prompt with context in XML format.
        """

        def dict_to_xml(d):
            """
            Convert a dictionary to an XML string.

            Args:
                d (dict): The dictionary to convert.

            Returns:
                str: The XML string representation of the dictionary.
            """
            xml = ""
            for key, value in d.items():
                if isinstance(value, dict):
                    xml += f"<{key}>{dict_to_xml(value)}</{key}>"
                else:
                    xml += f"<{key}>{value}</{key}>"
            return xml

        context_xml = ""
        if self.context:
            context_xml += "<context>"
            context_xml += dict_to_xml(self.context)
            context_xml += "</context>"

        user_prompt = f"<prompt>{self.prompt}</prompt>{context_xml}"
        return user_prompt


class AgentScope(BaseModel):
    """
    Scope of the agent's operation.

    Attributes:
        paths (list[str]): List of paths the agent can access.
        organization_id (str | None): The organization ID.
    """

    paths: list[str] = ["/"]
    organization_id: str | None = None


class AgentExecuteSequenceInput(UserPromptWithContext):
    """
    Input for executing a sequence of agent configurations.

    Attributes:
        agent_configs (list[AgentConfiguration] | None): List of agent configurations.
        scope (AgentScope): The scope of the agent's operation.
        prompt (str | None): The prompt to be executed.
    """

    agent_configs: list[AgentConfiguration] | None = [AgentConfiguration()]
    scope: AgentScope = AgentScope(paths=[], organization_id=None)


class AgentExecuteInput(UserPromptWithContext):
    """
    Input for executing an agent.

    Attributes:
        agent_config (AgentConfiguration): The configuration for the agent.
        scope (AgentScope): The scope of the agent's operation.
    """

    agent_config: AgentConfiguration = AgentConfiguration(agent_type=AgentType.DEFAULT)
    scope: AgentScope = AgentScope(paths=[], organization_id=None)


class AgentResult(BaseModel):
    """
    Result of an agent's execution.

    Attributes:
        result (str): The result of the agent's execution.
        search_results (list[SearchResults]): List of search results.
    """

    result: str
    search_results: list[SearchResults]


class AgentExecutionResponse(BaseModel):
    """
    Response from executing an agent.

    Attributes:
        result (str): The result of the agent's execution.
        agent_results (list[AgentResult]): List of agent results.
    """

    result: str
    agent_results: list[AgentResult]
