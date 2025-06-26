from app.api.auth import ApiKeyToken
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def ping(caller: ApiKeyToken) -> dict:
    return {"user_id": caller.user_id}
