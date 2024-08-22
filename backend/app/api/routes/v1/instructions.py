import logging

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
logger = logging.getLogger(__name__)



@router.post("/", response_model=ExecuteInstructionResponse, deprecated=True)
def execute_instruction(
    session: CurrentSession, body: ExecuteInstructionRequest, user: CurrentUser
) -> ExecuteInstructionResponse:
    requested_org = session.exec(
        select(Workspace).where(Workspace.id == body.workspace_id)
    ).first()
    if requested_org is None:
        logger.error(f"Workspace {body.workspace_id} not found")
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )
    if user.organization_id == requested_org.organization_id:
        call_id = modal_interface.execute_instruction(
            body.workspace_id, body.codebase_id, body.prompt
        )
        return ExecuteInstructionResponse(
            call_id=call_id,
        )
    logger.error(
        f"User {user.user_id} requested execution outside of their organization."
    )
    raise HTTPException(
        status_code=403,
        detail="Invalid organization provided",
    )

@router.post("/execute", response_model=ExecuteInstructionResponse, deprecated=True)
def execute_instruction(
    session: CurrentSession, body: ExecuteInstructionRequest, user: CurrentUser
) -> ExecuteInstructionResponse:
    requested_org = session.exec(
        select(Workspace).where(Workspace.id == body.workspace_id)
    ).first()
    if requested_org is None:
        logger.error(f"Workspace {body.workspace_id} not found")
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )
    if user.organization_id == requested_org.organization_id:
        call_id = modal_interface.execute_instruction(
            body.workspace_id, body.codebase_id, body.prompt
        )
        return ExecuteInstructionResponse(
            call_id=call_id,
        )
    logger.error(
        f"User {user.user_id} requested execution outside of their organization."
    )
    raise HTTPException(
        status_code=403,
        detail="Invalid organization provided",
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



