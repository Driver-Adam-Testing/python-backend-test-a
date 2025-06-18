from app.api.auth import ApiKeyToken
from app.services.auth0_service import Auth0Service
from fastapi import APIRouter

router = APIRouter()
auth0_service = Auth0Service()


@router.get("/me")
async def user_info(caller: ApiKeyToken) -> dict:
    return auth0_service.get_user_profile(caller.user_id)
