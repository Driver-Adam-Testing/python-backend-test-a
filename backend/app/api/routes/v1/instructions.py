from pydantic import BaseModel
from typing import List
from fastapi import APIRouter
from modal import Function
from modal.functions import FunctionCall
from app.core.config import settings

router = APIRouter()


class Instruction(BaseModel):
    call_id: str = None
    status: str = None
    response: str = None
    error: str = None


class ExecuteInstructionRequest(BaseModel):
    workspace_id: str
    codebase_id: str
    prompt: str


class ExecuteInstructionResponse(BaseModel):
    call_id: str = None


class BatchInstructionResultsRequest(BaseModel):
    call_ids: List[str]


class BatchInstructionResultsResponse(BaseModel):
    results: list[Instruction]


@router.post("/execute", response_model=ExecuteInstructionResponse)
def execute_instruction(body: ExecuteInstructionRequest) -> ExecuteInstructionResponse:
    workspace_id = body.workspace_id
    codebase_id = body.codebase_id
    prompt = body.prompt
    single_shot_edit = Function.lookup(
        "comprehender",
        "single_shot_edit",
        environment_name=settings.MODAL_ENVIRONMENT)

    call_response = single_shot_edit.spawn(
        str(workspace_id), str(codebase_id), prompt, None
    )

    if call_response is None:
        raise Exception("Failed to spawn function call")

    print(call_response)
    return ExecuteInstructionResponse(
        call_id=str(call_response.object_id),
    )


@router.post("/execution/results", response_model=BatchInstructionResultsResponse)
def execute_instruction(body: BatchInstructionResultsRequest) -> BatchInstructionResultsResponse:

    call_ids = body.call_ids

    results: [Instruction] = []

    for call_id in call_ids:
        instruction_result = Instruction(
            call_id=call_id,
        )
        function_call = FunctionCall.from_id(call_id)
        try:
            result = function_call.get(timeout=0)
            instruction_result.status = "completed"
            instruction_result.response = result.get("content")
        except TimeoutError:
            instruction_result.status = "running"
            instruction_result.response = ""

        print(instruction_result)

        results.append(instruction_result)
    #
    return BatchInstructionResultsResponse(
        results=results
    )
