import logging

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.api.auth import UserToken
from app.schemas.user_schema import MessageResponse
from app.services.auth0_factory import create_auth0_service

router = APIRouter()

logger = logging.getLogger(__name__)


@router.put(
    "/password",
    status_code=200,
)
def change_password(
    user: UserToken, authorization: str | None = Header(None)
) -> MessageResponse:
    logging.info(f"User-requested password reset from: {user.subject}")
    access_token = authorization.replace("Bearer ", "")
    try:
        auth0_service = create_auth0_service()
        return {
            "message": auth0_service.change_self_password(
                user=user,
                access_token=access_token,
            )
        }
    except Exception as e:
        logger.error(f"An error occurred getting user's information: {e}")
        raise HTTPException(500, "Unable to request password reset.")


class Branding(BaseModel):
    logo_url: None | str = None
    colors: None | dict[str, str] = None


class Metadata(BaseModel):
    org_logo_url: None | str = None


class Organization(BaseModel):
    id: str
    display_name: str
    name: str
    branding: Branding | None = None
    metadata: Metadata | None = None


class OrganizationsResponse(BaseModel):
    results: list[Organization]
    total_count: int


@router.get("/organizations", response_model=OrganizationsResponse)
def get_organizations(user: UserToken) -> OrganizationsResponse:
    auth0_service = create_auth0_service()
    organizations_data = auth0_service.list_user_organizations(user)
    return OrganizationsResponse(
        results=organizations_data.get("organizations", []),
        total_count=organizations_data.get("total", 0),
    )
