import logging

from fastapi import APIRouter, Header, HTTPException

from app.api.auth import UserToken
from app.schemas.user_schema import MessageResponse
from app.services.auth0_service import Auth0Service

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
        auth0_service = Auth0Service()
        return {
            "message": auth0_service.change_self_password(
                user=user,
                access_token=access_token,
            )
        }
    except Exception as e:
        logger.error(f"An error occurred getting user's information: {e}")
        raise HTTPException(500, "Unable to request password reset.")


@router.get(
    "/organizations",
    status_code=200,
)
def get_organizations(user: UserToken):  # noqa: ANN201 disable to proxy Auth0 any typed responses
    logging.info(f"User-requested password reset from: {user.subject}")
    try:
        auth0_service = Auth0Service()
        return auth0_service.list_organizations(user)
    except Exception as e:
        logger.error(f"An error occurred getting user's organizations: {e}")
        raise HTTPException(500, "Unable to fetch user's organizations.")
