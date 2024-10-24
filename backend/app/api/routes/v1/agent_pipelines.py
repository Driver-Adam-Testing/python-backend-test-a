from fastapi import APIRouter
from modal import Function
from modal.functions import FunctionCall
from pydantic import BaseModel
from shared.interfaces.agents.pipeline_configuration import (
    PipelineInput,
    PipelineResponse,
)
from shared.interfaces.request import DriverModalBatchRequest
from shared.interfaces.response import DriverModalResponse

from app.api.auth import UserToken

router = APIRouter()


@router.post(
    "/",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence(user: UserToken, input: PipelineInput) -> PipelineResponse:
    from shared.pipelines.agents.execute import execute_sequence

    input.scope.organization_id = user.organization_id
    return execute_sequence(input)


@router.post(
    "/async",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_async(
    user: UserToken, input: PipelineInput
) -> DriverModalResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(input)
    return DriverModalResponse(call_id=instance.object_id)


@router.get("/async/{call_id}")
def get_execution_results(user: UserToken, call_id: str) -> PipelineResponse:
    function_call = FunctionCall.from_id(call_id)
    result = function_call.get(timeout=0)
    return result


class BatchInput(BaseModel):
    call_ids: list[str]


# TODO: this url is poorly formatted. used to keep the same as instructions for rapid development
@router.post("/async/batch")
def get_batch_execution_results(
    user: UserToken, input: DriverModalBatchRequest
) -> dict:
    results = {}
    for call_id in input.call_ids:
        function_call = FunctionCall.from_id(call_id)
        # TODO: don't transform the output
        try:
            result = function_call.get(timeout=0)
            results[call_id] = {
                "call_id": call_id,
                "status": "completed",
                "response": result,
                "error": "",
            }
        except TimeoutError:
            results[call_id] = {
                "call_id": call_id,
                "status": "running",
                "response": None,
                "error": "",
            }
        except Exception as e:
            results[call_id] = {
                "call_id": call_id,
                "status": "expired",
                "response": None,
                "error": str(e),
            }
    return results


@router.post(
    "/sync",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_sync(
    user: UserToken, input: PipelineInput
) -> PipelineResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    result = modal_function.remote(input)
    return result
