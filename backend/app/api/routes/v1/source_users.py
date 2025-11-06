"""API routes for Source Users (Source ACL) management - Users only, not teams."""

import logging
from uuid import UUID

from database.models_enums import PrimaryAssetRole
from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.schemas.source_access_schema import (
    AccessType,
    AddSourceUsersRequest,
    RemoveSourceUsersRequest,
    SourceUsersResponse,
    UpdateSourceUsersRequest,
)
from app.services.source_access_service import SourceAccessService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/sources/{source_id}/users",
    response_model=SourceUsersResponse,
    summary="List all effective users with source access",
    description="Get paginated list of all users with effective access to a source (includes direct grants and team-based access)",
)
def get_source_users(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[PrimaryAssetRole] | None = Query(
        default=None, description="Filter by source access roles"
    ),
    search: str | None = Query(default=None, description="Search by name or email"),
    access_type: AccessType | None = Query(
        default=None, description="Filter by access type: 'direct' or 'inherited'"
    ),
) -> SourceUsersResponse:
    enforce_asset_action(session, user, source_id, "asset.use_as_source")
    logger.info(
        f"User {user.user_id} getting users for source {source_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search}, access_type={access_type})"
    )
    service = SourceAccessService(session)
    return service.get_source_users(
        user=user,
        source_id=source_id,
        roles=roles,
        search=search,
        access_type=access_type,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/sources/{source_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add users to source",
    description="Grant users (not teams) access to a source with specific roles",
)
def add_source_users(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: AddSourceUsersRequest,
) -> None:
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} adding {len(request.users)} users to source {source_id}"
    )
    service = SourceAccessService(session)
    service.add_source_users(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.put(
    "/sources/{source_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update source user roles",
    description="Update roles for source's existing users (not teams)",
)
def update_source_users(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: UpdateSourceUsersRequest,
) -> None:
    """
    Update roles for source's users.

    - **users**: List of users (not teams) with updated roles
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} updating {len(request.users)} users for source {source_id}"
    )
    service = SourceAccessService(session)
    service.update_source_users(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.delete(
    "/sources/{source_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove users from source",
    description="Revoke user (not team) access to a source",
)
def remove_source_users(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: RemoveSourceUsersRequest,
) -> None:
    """
    Remove users from a source.

    - **user_ids**: List of user IDs to remove
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} removing {len(request.user_ids)} users from source {source_id}"
    )
    service = SourceAccessService(session)
    service.remove_source_users(
        user=user,
        source_id=source_id,
        request=request,
    )
