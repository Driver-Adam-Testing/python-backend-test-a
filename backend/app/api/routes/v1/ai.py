from fastapi import APIRouter
from modal import Function
from shared.interfaces.response import ModalDriverResponse
from shared.pipelines.agents.execute import (
    AgentExecuteInput,
    AgentExecutionResponse,
    AgentExecutionSequenceResponse,
    execute_sequence,
    execute_single,
)

from app.api.auth import CurrentUser

router = APIRouter()


@router.post(
    "/",
    summary="Execute an agent pipeline",
    response_description="The response from the agent execution",
)
def execute_agent(
    user: CurrentUser,
    input: AgentExecuteInput,
) -> AgentExecutionResponse:
    input.scope.organization_id = user.organization_id
    return execute_single(input)


@router.post(
    "/sequence",
    summary="Execute an agent pipeline",
    response_description="The response from the agent execution",
)
def execute_agent_sequence(
    user: CurrentUser,
    input: AgentExecuteInput,
) -> AgentExecutionSequenceResponse:
    input.scope.organization_id = user.organization_id
    return execute_sequence(input)


@router.post(
    "/sequence/modal/async",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_async(
    user: CurrentUser, input: AgentExecuteInput
) -> ModalDriverResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(input)
    return ModalDriverResponse(call_id=instance.object_id)


@router.post(
    "/sequence/modal", summary="Start a modal instance of the execute Agent Sequence"
)
def execute_agent_sequence_modal_sync(
    user: CurrentUser, input: AgentExecuteInput
) -> AgentExecutionSequenceResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    return modal_function.remote(input)
