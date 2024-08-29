import enum

import shared.agent.tools.agent_tools as agent_tools
from pydantic import BaseModel
from shared.agent.tools.tool import Tool
from shared.interfaces.search import SearchResults


class AgentType(enum.Enum):
    DEFAULT = "default"
    PROMPT_AUGMENTATION = "prompt_augmentation"
    COPY_EDITOR = "copy_editor"
    CODE_CRITIC = "code_critic"


class ToolConfig(BaseModel):
    name: str


class AgentConfiguration(BaseModel):
    model: str | None = None
    system_prompts: list[str] | None = None
    user_prompt: str | None = None
    agent_type: AgentType = AgentType.DEFAULT
    iterations: int = 1
    tools: list[ToolConfig] = []

    def get_tool_functions(self) -> list[Tool]:
        tools = []
        for tool_name in [t.name for t in self.tools]:
            if hasattr(agent_tools, tool_name):
                tool = getattr(agent_tools, tool_name)
                if isinstance(tool, Tool):
                    tools.append(tool)
                else:
                    raise TypeError(f"{tool_name} is not an instance of Tool")
            else:
                raise AttributeError(f"{tool_name} does not exist in agent_tools")
        return tools


class UserPromptWithContext(BaseModel):
    prompt: str
    context: list[str]

    def create_user_prompt(self):
        context_xml = ""
        if self.context:
            context_xml += "<context>"
            for ctx in reversed(self.context):
                context_xml += f"<context_chunk>{ctx}</context_chunk>"
            context_xml += "</context>"

        user_prompt = f"<prompt>{self.prompt}</prompt>{context_xml}"
        return user_prompt


class AgentScope(BaseModel):
    paths: list[str] = ["/"]
    organization_id: str | None = None


class AgentExecuteSequenceInput(BaseModel):
    agent_configs: list[AgentConfiguration] | None = [AgentConfiguration()]
    scope: AgentScope = AgentScope(paths=[], organization_id=None)
    prompt: str | None


class AgentExecuteInput(UserPromptWithContext):
    agent_config: AgentConfiguration = AgentConfiguration(agent_type=AgentType.DEFAULT)
    scope: AgentScope = AgentScope(paths=[], organization_id=None)


class AgentResult(BaseModel):
    result: str
    search_results: list[SearchResults]


class AgentExecutionResponse(BaseModel):
    result: str
    agent_results: list[AgentResult]
