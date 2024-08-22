from fastapi import APIRouter
from shared.pipelines.agents.execute import (
    AgentExecutionConfiguration,
    AgentExecutionResponse,
    execute,
)

from app.api.auth import CurrentUser

router = APIRouter()


@router.post(
    "/",
    summary="Execute an agent pipeline",
    response_description="The response from the agent execution",
)
def execute_agent_pipeline(
    user: CurrentUser,
    input: AgentExecutionConfiguration,
) -> AgentExecutionResponse:
    input.scope.organization_id = user.organization_id
    return execute(input)
