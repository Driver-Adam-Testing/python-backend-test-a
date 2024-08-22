from pydantic import BaseModel


class PromptConfiguration(BaseModel):
    name: str
    data: dict


class AgentConfiguration(BaseModel):
    model: str
    prompts: list[PromptConfiguration]


class AgentScope(BaseModel):
    paths: list[str]
    organization_id: str


class AgentExecutionConfiguration(BaseModel):
    configs: list[AgentConfiguration]
    agent_scope: AgentScope


def execute(input: AgentExecutionConfiguration):
    print(input)
    return True
