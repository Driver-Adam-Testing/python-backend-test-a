from fastapi import APIRouter
from modal import Function
from modal.functions import FunctionCall

from app.api.auth import CurrentUser

router = APIRouter()


# TODO: Change all this to not dicts.


@router.post(
    "/async",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_async(user: CurrentUser, input: dict) -> dict:
    input["scope"]["organization_id"] = user.organization_id
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(input)
    return {"call_id": instance.object_id}


@router.post("/async/batch")
def get_batch_execution_results(user: CurrentUser, call_ids: list[str]) -> dict:
    results = {}
    for call_id in call_ids:
        function_call = FunctionCall.from_id(call_id)
        # TODO: don't transform the output
        try:
            result = function_call.get(timeout=0)
            results[call_id] = {
                "call_id": call_id,
                "status": "completed",
                "response": result["content"],
                "error": "",
            }
        except TimeoutError:
            results[call_id] = {
                "call_id": call_id,
                "status": "running",
                "response": None,
                "error": "Request Timeout",
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
def execute_agent_sequence_modal_sync(user: CurrentUser, input: dict) -> dict:
    input["scope"]["organization_id"] = user.organization_id
    modal_function = Function.lookup("agent", "run")
    return modal_function.remote(input)
