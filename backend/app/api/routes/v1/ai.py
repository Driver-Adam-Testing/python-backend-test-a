import json

from fastapi import APIRouter, HTTPException
from modal import Function
from modal.functions import FunctionCall
from shared.interfaces.response import ModalDriverResponse
from shared.pipelines.agents.execute import (
    PipelineInput,
    PipelineResponse,
    execute_sequence,
)

from app.api.auth import CurrentUser

router = APIRouter()


@router.post(
    "/sequence",
    summary="Execute an agent pipeline",
    response_description="The response from the agent execution",
)
def execute_agent_sequence(
    user: CurrentUser,
    input: PipelineInput,
) -> PipelineResponse:
    input.scope.organization_id = user.organization_id
    return execute_sequence(input)


@router.post(
    "/sequence/modal/async",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_async(
    user: CurrentUser, input: PipelineInput
) -> ModalDriverResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(input)
    return ModalDriverResponse(call_id=instance.object_id)


@router.post("/results", response_model=PipelineResponse)
def get_execution_results(user: CurrentUser, call_id: str) -> PipelineResponse:
    function_call = FunctionCall.from_id(call_id)
    try:
        result = function_call.get(timeout=0)
        response = PipelineResponse(**json.loads(result))
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Request Timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response


@router.post(
    "/sequence/modal/sync",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_sync(
    user: CurrentUser, input: PipelineInput
) -> PipelineResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    return modal_function.remote(input)
