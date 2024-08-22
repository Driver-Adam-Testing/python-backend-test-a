from fastapi import APIRouter
from shared.interfaces.search import SearchResults
from shared.pipelines.agents.execute import AgentExecutionConfiguration, execute

router = APIRouter()


@router.post(
    "/",
    summary="Execute an Agent Pipeline",
    response_description="Return Search Results",
)
def execute_agent_pipeline(input: AgentExecutionConfiguration) -> SearchResults:
    # TODO: figure out how to do this without transforming the input.

    return execute(input)
