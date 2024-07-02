from typing import Any
from uuid import UUID

from database.models_v1 import Workspace
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.auth import CurrentUser
from app.api.session import CurrentSession

router = APIRouter()


class WorkspacesOut(BaseModel):
    data: list[Workspace] = []
    count: int


class WorkspaceOut(BaseModel):
    data: Workspace


class Message(BaseModel):
    message: str


@router.get("/", response_model=WorkspacesOut)
def read_workspaces(
    session: CurrentSession, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve workspaces.
    """
    statement = (
        select(Workspace)
        .where(Workspace.organization_id == current_user.organization_id)
        .offset(skip)
        .limit(limit)
    )
    workspaces = session.exec(statement).all()

    return WorkspacesOut(data=list(workspaces), count=len(workspaces))


@router.get("/{id}", response_model=Workspace)
def read_workspace(session: CurrentSession, current_user: CurrentUser, id: UUID) -> Any:
    """
    Get workspace by ID.
    """
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.organization_id != current_user.organization_id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return workspace


@router.post("/", response_model=Workspace)
def create_workspace(
    session: CurrentSession, current_user: CurrentUser, workspace: Workspace
) -> Any:
    """
    Create a new workspace.
    """
    workspace.id = None
    workspace.created_at = None
    workspace.updated_at = None
    new_workspace = Workspace(
        **workspace.__dict__, organization_id=current_user.organization_id
    )
    session.add(new_workspace)
    session.commit()
    return new_workspace


@router.put("/{id}", response_model=Workspace)
def update_workspace(
    session: CurrentSession, current_user: CurrentUser, id: UUID, workspace: Workspace
) -> Any:
    """
    Update an existing workspace.
    """
    existing_workspace = session.get(Workspace, id)
    if not existing_workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if existing_workspace.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    existing_workspace.display_name = workspace.display_name
    existing_workspace.description = workspace.description
    existing_workspace.organization_id = workspace.organization_id
    session.commit()
    return existing_workspace


@router.delete("/{id}", response_model=None)
def delete_workspace(
    session: CurrentSession, current_user: CurrentUser, id: UUID
) -> Any:
    """
    Delete a workspace.
    """
    workspace = session.get(Workspace, id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Workspace not found")

    session.delete(workspace)
    session.commit()
    return None
