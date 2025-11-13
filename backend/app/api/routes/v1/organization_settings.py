import logging

from database.models_enums import SourceVisibility
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_super_admin
from app.repositories import organization_repository
from app.schemas.common import validate_visibility_not_public

router = APIRouter()
logger = logging.getLogger(__name__)


class DefaultSourceVisibilityResponse(BaseModel):
    default_source_visibility: SourceVisibility = Field(
        ..., description="Default visibility for new sources"
    )


class UpdateDefaultSourceVisibilityRequest(BaseModel):
    default_source_visibility: SourceVisibility = Field(
        ..., description="New default visibility for sources (public not yet supported)"
    )

    _validate_not_public = field_validator("default_source_visibility")(
        validate_visibility_not_public
    )


@router.get(
    "/default-source-visibility",
    response_model=DefaultSourceVisibilityResponse,
    summary="Get default source visibility",
    description="Get the default visibility setting for new sources. Only accessible by org super admin.",
)
def get_default_source_visibility(
    session: CurrentSession,
    user: UserToken,
) -> DefaultSourceVisibilityResponse:
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} getting default source visibility "
        f"for org {user.organization_id}"
    )

    visibility = organization_repository.get_default_source_visibility(
        session, user.organization_id
    )
    return DefaultSourceVisibilityResponse(default_source_visibility=visibility)


@router.put(
    "/default-source-visibility",
    response_model=DefaultSourceVisibilityResponse,
    summary="Update default source visibility",
    description="Update the default visibility setting for new sources. Only accessible by org super admin.",
)
def update_default_source_visibility(
    request: UpdateDefaultSourceVisibilityRequest,
    session: CurrentSession,
    user: UserToken,
) -> DefaultSourceVisibilityResponse:
    enforce_super_admin(session, user)
    logger.info(
        f"User {user.user_id} updating default source visibility to "
        f"{request.default_source_visibility} for org {user.organization_id}"
    )

    visibility = organization_repository.update_default_source_visibility(
        session, user.organization_id, request.default_source_visibility
    )
    return DefaultSourceVisibilityResponse(default_source_visibility=visibility)
