from app.api.auth import ApiKeyToken
from app.services.auth0_factory import create_auth0_service
from fastapi import APIRouter

router = APIRouter()
auth0_service = create_auth0_service()


@router.get("/me")
async def user_info(caller: ApiKeyToken) -> dict:
    return auth0_service.get_user_profile(caller.user_id)


@router.get("/me/organization")
async def user_organization(caller: ApiKeyToken) -> dict:
    return auth0_service.get_organization(caller.organization_id)
