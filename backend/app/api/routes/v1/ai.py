from fastapi import APIRouter
from shared.pipelines.agents.execute import (
    AgentExecutionConfiguration,
    AgentExecutionResponse,
    execute,
)

router = APIRouter()


@router.post(
    "/",
    summary="Execute an agent pipeline",
    response_description="The response from the agent execution",
)
def execute_agent_pipeline(
    input: AgentExecutionConfiguration,
) -> AgentExecutionResponse:
    return execute(input)
