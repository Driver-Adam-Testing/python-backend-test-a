"""API routes for User Sources management."""

import logging

from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.schemas.user_schema import (
    AddUserSourcesRequest,
    RemoveUserSourcesRequest,
    UpdateUserSourcesRequest,
    UserSourcesResponse,
)
from app.services.user_service import UserService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/{user_id}/sources",
    response_model=UserSourcesResponse,
    summary="Get user's sources",
    description="Get paginated list of sources (codebases/files) that a user has direct access to",
)
def get_user_sources(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    limit: int = Query(
        default=30, ge=1, le=100, description="Maximum number of results"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    roles: list[str] | None = Query(
        default=None, description="Filter by roles: admin, member"
    ),
    search: str | None = Query(default=None, description="Search by display name"),
) -> UserSourcesResponse:
    """
    Get paginated list of sources for a user.

    Returns sources with role and visibility information.
    """
    logger.info(
        f"User {user.user_id} getting sources for user {user_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = UserService(session)
    return service.get_user_sources(
        user_id=user_id,
        organization_id=user.organization_id,
        roles=roles,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{user_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Grant user direct access to sources",
    description="Grant user direct access to sources with specific roles",
)
def add_user_sources(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: AddUserSourcesRequest,
) -> None:
    """
    Grant user direct access to sources.

    - **sources**: List of sources with roles to grant access to
    """
    logger.info(
        f"User {user.user_id} granting user {user_id} access to {len(request.sources)} sources"
    )
    service = UserService(session)
    service.add_user_sources(
        user_id=user_id,
        organization_id=user.organization_id,
        request=request,
    )


@router.put(
    "/{user_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user's source roles",
    description="Update roles for user's existing sources",
)
def update_user_sources(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: UpdateUserSourcesRequest,
) -> None:
    """
    Update user's source roles.

    - **sources**: List of sources with updated roles
    """
    logger.info(
        f"User {user.user_id} updating roles for user {user_id} on {len(request.sources)} sources"
    )
    service = UserService(session)
    service.update_user_sources(
        user_id=user_id,
        organization_id=user.organization_id,
        request=request,
    )


@router.delete(
    "/{user_id}/sources",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove user's direct access to sources",
    description="Remove user's direct access to specified sources",
)
def remove_user_sources(
    session: CurrentSession,
    user: UserToken,
    user_id: str,
    request: RemoveUserSourcesRequest,
) -> None:
    """
    Remove user's direct access to sources.

    - **source_ids**: List of source IDs to remove access from
    """
    logger.info(
        f"User {user.user_id} removing user {user_id} access from {len(request.source_ids)} sources"
    )
    service = UserService(session)
    service.remove_user_sources(
        user_id=user_id,
        organization_id=user.organization_id,
        request=request,
    )
