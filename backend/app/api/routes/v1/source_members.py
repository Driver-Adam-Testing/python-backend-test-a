"""API routes for Source Members (Source ACL) management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.source_access_schema import (
    AddSourceMembersRequest,
    RemoveSourceMembersRequest,
    SourceMembersResponse,
    UpdateSourceMembersRequest,
)
from app.services.source_access_service import SourceAccessService
from app.authorization.fastapi import enforce_asset_action

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/sources/{source_id}/members",
    response_model=SourceMembersResponse,
    summary="List source members",
    description="Get paginated list of members (users and teams) that have access to a source",
)
def get_source_members(
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
    member_kind: str | None = Query(
        default=None, description="Filter by member type: user, team"
    ),
    search: str | None = Query(
        default=None, description="Search by name or email (for users)"
    ),
) -> SourceMembersResponse:
    """
    Get paginated list of members for a source.

    Returns both users and teams with their roles and access details.
    """
    enforce_asset_action(session, user, source_id, "asset.use_as_source")
    logger.info(
        f"User {user.user_id} getting members for source {source_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, kind={member_kind}, search={search})"
    )
    service = SourceAccessService(session)
    return service.get_source_members(
        user=user,
        source_id=source_id,
        roles=roles,
        member_kind=member_kind,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/sources/{source_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add members to source",
    description="Grant members (users or teams) access to a source with specific roles",
)
def add_source_members(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: AddSourceMembersRequest,
) -> None:
    """
    Add members to a source.

    - **members**: List of members (users or teams) with roles to grant
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} adding {len(request.members)} members to source {source_id}"
    )
    service = SourceAccessService(session)
    service.add_source_members(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.put(
    "/sources/{source_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update source member roles",
    description="Update roles for source's existing members",
)
def update_source_members(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: UpdateSourceMembersRequest,
) -> None:
    """
    Update roles for source's members.

    - **members**: List of members with updated roles
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} updating {len(request.members)} members for source {source_id}"
    )
    service = SourceAccessService(session)
    service.update_source_members(
        user=user,
        source_id=source_id,
        request=request,
    )


@router.delete(
    "/sources/{source_id}/members",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove members from source",
    description="Revoke member (user or team) access to a source",
)
def remove_source_members(
    session: CurrentSession,
    user: UserToken,
    source_id: UUID,
    request: RemoveSourceMembersRequest,
) -> None:
    """
    Remove members from a source.

    - **members**: List of members to remove (with member_id and kind)
    """
    enforce_asset_action(session, user, source_id, "asset.manage")
    logger.info(
        f"User {user.user_id} removing {len(request.members)} members from source {source_id}"
    )
    service = SourceAccessService(session)
    service.remove_source_members(
        user=user,
        source_id=source_id,
        request=request,
    )
