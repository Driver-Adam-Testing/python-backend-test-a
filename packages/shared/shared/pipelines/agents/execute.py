from pydantic import BaseModel
from shared.agent.agent import OpenAIAgent


class PromptConfiguration(BaseModel):
    name: str
    data: dict


class AgentConfiguration(BaseModel):
    model: str | None = None
    prompt: str | None
    prompts: list[PromptConfiguration] | None = None


class AgentScope(BaseModel):
    paths: list[str]
    organization_id: str | None = None


class AgentExecutionConfiguration(BaseModel):
    agent_configs: list[AgentConfiguration] | None = None
    agent_scope: AgentScope = AgentScope(paths=[], organization_id=None)
    prompt_meta: dict | None = None


class AgentExecutionResponse(BaseModel):
    result: str


def execute(input: AgentExecutionConfiguration):
    working_document = ""
    for agent_config in input.agent_configs:
        agent = OpenAIAgent(model=agent_config.model)
        working_document += agent.invoke(agent_config.prompt)
    return AgentExecutionResponse(result="done")
