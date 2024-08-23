import enum

import shared.agent.tools.agent_tools as agent_tools
from pydantic import BaseModel
from shared.agent.agent_factory import create_agent
from shared.agent.tools.tool import Tool
from shared.interfaces.search import SearchResults


class PromptConfiguration(BaseModel):
    name: str
    data: dict


class AgentType(enum.Enum):
    DEFAULT = "default"
    PROMPT_AUGMENTATION = "prompt_augmentation"


class ToolConfig(BaseModel):
    name: str


class AgentConfiguration(BaseModel):
    model: str | None = None
    additional_prompt: str | None = None
    prompts: list[PromptConfiguration] | None = None
    system_prompts: dict | None = None
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


class AgentScope(BaseModel):
    paths: list[str] = ["/"]
    organization_id: str | None = None


class AgentExecuteSequenceInput(BaseModel):
    agent_configs: list[AgentConfiguration] | None = [
        AgentConfiguration(agent_type=AgentType.DEFAULT)
    ]
    scope: AgentScope = AgentScope(paths=[], organization_id=None)
    prompt: str | None


class AgentResult(BaseModel):
    result: str
    search_results: list[SearchResults]


class AgentExecutionResponse(BaseModel):
    result: str
    agent_results: list[AgentResult]


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


def execute_sequence(input: AgentExecuteSequenceInput):
    user_prompt = UserPromptWithContext(prompt=input.prompt, context=[])
    output = input.prompt
    agent_results = []

    for agent_config in input.agent_configs:
        if output:
            user_prompt.prompt = output
        user_prompt.prompt = (
            agent_config.additional_prompt if agent_config.additional_prompt else output
        )

        if agent_config.agent_type == AgentType.DEFAULT:
            output = run_agent_default(
                prompt=user_prompt.create_user_prompt(),
                agent_config=agent_config,
                scope=input.scope,
            )
        if agent_config.agent_type == AgentType.PROMPT_AUGMENTATION:
            output = run_agent_prompt_augmentation(
                prompt=user_prompt.create_user_prompt(),
                agent_config=agent_config,
                scope=input.scope,
            )
        agent_results.append(output)

    return AgentExecutionResponse(
        result=agent_results[-1].result, agent_results=agent_results
    )


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

    response = agent.invoke(
        f"Return only a rewritten prompt for the following: \n\n{prompt}\n\n To better address the type of request that the user probably wants. Keep in mind that they may want a short or long response."
    )
    return AgentResult(result=response, search_results=agent.search_results)


def run_agent_default(prompt: str, agent_config: AgentConfiguration, scope: AgentScope):
    agent = create_agent(
        model=agent_config.model,
        organization_id=scope.organization_id,
        max_iterations=agent_config.iterations,
        tools=agent_config.get_tool_functions(),
        paths=scope.paths,
    )
    response = agent.invoke(prompt)
    return AgentResult(result=response, search_results=agent.search_results)
