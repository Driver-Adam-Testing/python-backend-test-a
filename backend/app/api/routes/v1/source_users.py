"""API routes for Source Users (Source ACL) management - Users only, not teams."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.schemas.source_access_schema import (
    AddSourceUsersOnlyRequest,
    AddSourceUsersRequest,
    RemoveSourceUserInput,
    RemoveSourceUsersOnlyRequest,
    RemoveSourceUsersRequest,
    SourceUserInput,
    SourceUsersResponse,
    UpdateSourceUsersOnlyRequest,
    UpdateSourceUsersRequest,
)
from app.services.source_access_service import SourceAccessService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/sources/{source_id}/users",
    response_model=SourceUsersResponse,
    summary="List source users",
    description="Get paginated list of users (not teams) that have access to a source",
)
def get_source_users(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[str] | None = Query(
        default=None, description="Filter by roles: admin, member"
    ),
    search: str | None = Query(default=None, description="Search by name or email"),
) -> SourceUsersResponse:
    """
    Get paginated list of users for a source.

    Returns only users (not teams) with their roles and access details.
    """
    enforce_asset_action(session, user, source_id, "asset.use_as_source")
    logger.info(
        f"User {user.user_id} getting users for source {source_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = SourceAccessService(session)
    return service.get_source_users(
        user=user,
        source_id=source_id,
        roles=roles,
        user_kind="user",  # Hardcoded to only return users
        search=search,
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
    request: AddSourceUsersOnlyRequest,
) -> None:
    """
    Add users to a source.

    - **users**: List of users (not teams) with roles to grant
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} adding {len(request.users)} users to source {source_id}"
    )
    service = SourceAccessService(session)
    # Convert to the format expected by service
    converted_request = AddSourceUsersRequest(
        users=[
            SourceUserInput(user_id=u.user_id, kind="user", role=u.role)
            for u in request.users
        ]
    )
    service.add_source_users(
        user=user,
        source_id=source_id,
        request=converted_request,
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
    request: UpdateSourceUsersOnlyRequest,
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
    # Convert to the format expected by service
    converted_request = UpdateSourceUsersRequest(
        users=[
            SourceUserInput(user_id=u.user_id, kind="user", role=u.role)
            for u in request.users
        ]
    )
    service.update_source_users(
        user=user,
        source_id=source_id,
        request=converted_request,
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
    request: RemoveSourceUsersOnlyRequest,
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
    # Convert to the format expected by service
    converted_request = RemoveSourceUsersRequest(
        users=[
            RemoveSourceUserInput(user_id=uid, kind="user") for uid in request.user_ids
        ]
    )
    service.remove_source_users(
        user=user,
        source_id=source_id,
        request=converted_request,
    )
