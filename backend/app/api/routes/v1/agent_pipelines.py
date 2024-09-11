from fastapi import APIRouter, HTTPException
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


@router.get("/async/{call_id}")
def get_execution_results(user: CurrentUser, call_id: str) -> dict:
    function_call = FunctionCall.from_id(call_id)
    try:
        result = function_call.get(timeout=0)
        return result.model_dump()
    except TimeoutError:
        raise HTTPException(status_code=408, detail="Request Timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/sync",
    summary="Start a modal instance of the execute Agent Sequence",
)
def execute_agent_sequence_modal_sync(user: CurrentUser, input: dict) -> dict:
    input["scope"]["organization_id"] = user.organization_id
    modal_function = Function.lookup("agent", "run")
    return modal_function.remote(input).model_dump()
