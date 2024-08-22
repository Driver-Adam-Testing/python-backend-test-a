from database.models_v1 import Workspace
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.instructions import modal_interface
from app.instructions.types import (
    BatchInstructionResultsRequest,
    ExecuteInstructionRequest,
    ExecuteInstructionResponse,
    InstructionResultsResponse,
)

router = APIRouter()


@router.post("/execute", response_model=ExecuteInstructionResponse)
def execute_instruction(
    session: CurrentSession, body: ExecuteInstructionRequest, user: CurrentUser
) -> ExecuteInstructionResponse:
    try:
        requested_org_id = (
            session.exec(select(Workspace).where(Workspace.id == body.workspace_id))
            .first()
            .organization_id
        )
        if user.organization_id == requested_org_id:
            call_id = modal_interface.execute_instruction(
                body.workspace_id, body.codebase_id, body.prompt
            )
            return ExecuteInstructionResponse(
                call_id=call_id,
            )
        raise HTTPException(
            status_code=403,
            detail="Invalid organization provided",
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        ) from e


@router.post("/results", response_model=InstructionResultsResponse)
def get_execution_results(
    body: BatchInstructionResultsRequest, user: CurrentUser
) -> InstructionResultsResponse:
    batch_results = modal_interface.get_batch_execution_results(body.call_ids)
    return InstructionResultsResponse(data=batch_results)
