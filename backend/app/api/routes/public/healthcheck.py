from datetime import datetime

from app.api.auth import UserToken
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def healthcheck() -> None:
    return {
        "status": f"healthy - but unsure of myself. (how relatable) it's {datetime.now()}"
    }


@router.get("/user_info")
async def user_info(user: UserToken) -> UserToken:
    return user
