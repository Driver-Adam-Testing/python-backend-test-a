"""API routes for User Sources management."""

import logging
import uuid

from database.models_enums import PrimaryAssetRole
from fastapi import APIRouter, Query, status

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action, enforce_org_action
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
    roles: list[PrimaryAssetRole] | None = Query(
        default=None, description="Filter by roles: asset_admin, asset_viewer"
    ),
    search: str | None = Query(default=None, description="Search by display name"),
) -> UserSourcesResponse:
    """
    Get paginated list of sources for a user.

    Returns sources with role and visibility information.
    """
    # Assuming the service is doing its job and only fetching sources that
    # this user has access to, the only enforcement is that the user is
    # a member of the organization. Is this enough?
    enforce_org_action(session, user, "users.view")
    logger.info(
        f"User {user.user_id} getting sources for user {user_id} "
        f"(limit={limit}, offset={offset}, roles={roles}, search={search})"
    )
    service = UserService(session)
    return service.get_user_sources(
        user=user,
        user_id=user_id,
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
    for source in request.sources:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source.source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} granting user {user_id} access to {len(request.sources)} sources"
    )
    service = UserService(session)
    service.add_user_sources(
        user=user,
        user_id=user_id,
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
    for source in request.sources:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source.source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} updating roles for user {user_id} on {len(request.sources)} sources"
    )
    service = UserService(session)
    service.update_user_sources(
        user=user,
        user_id=user_id,
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
    for source_id in request.source_ids:
        enforce_asset_action(
            session,
            user,
            uuid.UUID(source_id),
            "asset.manage",
        )
    logger.info(
        f"User {user.user_id} removing user {user_id} access from {len(request.source_ids)} sources"
    )
    service = UserService(session)
    service.remove_user_sources(
        user=user,
        user_id=user_id,
        request=request,
    )
