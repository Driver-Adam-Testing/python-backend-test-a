import logging

from database.models_v1 import Workspace, Codebase
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
logger = logging.getLogger(__name__)


@router.post("/execute", response_model=ExecuteInstructionResponse)
def execute_instruction(
    session: CurrentSession, body: ExecuteInstructionRequest, user: CurrentUser
) -> ExecuteInstructionResponse:
    result = session.exec(
        select(Workspace, Codebase)
        .where(Workspace.id == body.workspace_id)
        .where(Workspace.organization_id == user.organization_id)
        .where(Codebase.id == body.codebase_id)
        .where(Codebase.workspace_id == body.workspace_id)
    ).first()
    
    if not result:
        logger.error(f"Invalid workspace or codebase for workspace_id {body.workspace_id} and codebase_id {body.codebase_id}")
        raise HTTPException(status_code=400, detail="Invalid workspace or codebase")

    call_id = modal_interface.execute_instruction(
        str(body.workspace_id), str(body.codebase_id), body.prompt
    )
    return ExecuteInstructionResponse(call_id=call_id)


@router.post("/results", response_model=InstructionResultsResponse)
def get_execution_results(
    body: BatchInstructionResultsRequest, user: CurrentUser
) -> InstructionResultsResponse:
    batch_results = modal_interface.get_batch_execution_results(body.call_ids)
    return InstructionResultsResponse(data=batch_results)