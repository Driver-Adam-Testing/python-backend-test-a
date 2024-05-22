from fastapi import APIRouter, Depends

from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", status_code=200)
def secure_endpoint(user: dict = Depends(get_current_user)):
    return {"message": "Authenticated", "user": user}
