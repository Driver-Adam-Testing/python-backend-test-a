from uuid import UUID

from database.models_v1 import Workspace
from sqlmodel import Session

from app.api.auth import CurrentUser
from app.api.routes.v1.workspace import (
    WorkspacesOut,
    create_workspace,
    delete_workspace,
    read_workspace,
    read_workspaces,
    update_workspace,
)
from app.tests.utils.workspace import random_workspace


def test_create_workspace(db: Session, current_user_with_org: CurrentUser) -> None:
    workspace = random_workspace()
    created_workspace = create_workspace(db, current_user_with_org, workspace)
    assert created_workspace.display_name == workspace.display_name
    assert created_workspace.description == workspace.description
    assert isinstance(created_workspace.id, UUID)
    assert created_workspace.organization_id == current_user_with_org.organization_id


def test_read_workspaces(db: Session, current_user_with_org: CurrentUser) -> None:
    workspace = random_workspace(current_user_with_org.organization_id)
    db.add(workspace)
    db.commit()
    workspaces = read_workspaces(db, current_user_with_org, skip=0, limit=100)
    assert isinstance(workspaces, WorkspacesOut)
    assert len(workspaces.data) > 0
    assert workspaces.count == len(workspaces.data)


def test_read_workspace(db: Session, current_user_with_org: CurrentUser) -> None:
    workspace = random_workspace(current_user_with_org.organization_id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    workspace_from_read = read_workspace(db, current_user_with_org, workspace.id)
    assert isinstance(workspace_from_read, Workspace)
    assert workspace_from_read.id == workspace.id
    assert workspace_from_read.display_name == workspace.display_name
    assert workspace_from_read.description == workspace.description
    assert workspace_from_read.organization_id == workspace.organization_id


def test_update_workspace(db: Session, current_user_with_org: CurrentUser) -> None:
    workspace = random_workspace(current_user_with_org.organization_id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    updated_workspace_data = random_workspace(current_user_with_org.organization_id)
    updated_workspace_data.id = workspace.id
    updated_workspace = update_workspace(
        db, current_user_with_org, workspace.id, updated_workspace_data
    )
    assert isinstance(updated_workspace, Workspace)
    assert updated_workspace.id == workspace.id
    assert updated_workspace.display_name == updated_workspace_data.display_name
    assert updated_workspace.description == updated_workspace_data.description
    assert updated_workspace.organization_id == workspace.organization_id


def test_delete_workspace(db: Session, current_user_with_org: CurrentUser) -> None:
    workspace = random_workspace(current_user_with_org.organization_id)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    delete_workspace(db, current_user_with_org, workspace.id)
    deleted_workspace = db.get(Workspace, workspace.id)
    assert deleted_workspace is None
