from fastapi import APIRouter
from app.instructions.types import (
    ExecuteInstructionRequest,
    ExecuteInstructionResponse,
    BatchInstructionResultsRequest,
    InstructionResultsResponse,
    Instruction
)
from app.instructions import modal_interface

router = APIRouter()


@router.post("/", response_model=ExecuteInstructionResponse)
def create_instruction(body: ExecuteInstructionRequest) -> ExecuteInstructionResponse:
    call_id = modal_interface.execute_instruction(body.workspace_id, body.codebase_id, body.prompt)
    return ExecuteInstructionResponse(
        call_id=call_id,
    )

#TODO deprecated
@router.post("/execute", response_model=ExecuteInstructionResponse, deprecated=True)
def execute_instruction(body: ExecuteInstructionRequest) -> ExecuteInstructionResponse:
    call_id = modal_interface.execute_instruction(body.workspace_id, body.codebase_id, body.prompt)
    return ExecuteInstructionResponse(
        call_id=call_id,
    )


#TODO deprecated
@router.post("/results", response_model=InstructionResultsResponse, deprecated=True)
def get_execution_results(body: BatchInstructionResultsRequest) -> InstructionResultsResponse:
    batch_results = modal_interface.get_batch_execution_results(body.call_ids)
    return InstructionResultsResponse(
        data=batch_results
    )


@router.post("/results/search", response_model=InstructionResultsResponse)
def get_execution_search_results(body: BatchInstructionResultsRequest) -> InstructionResultsResponse:
    batch_results = modal_interface.get_batch_execution_results(body.call_ids)
    return InstructionResultsResponse(
        data=batch_results
    )