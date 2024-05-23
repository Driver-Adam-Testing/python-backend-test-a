from fastapi import APIRouter

from app.api.auth import CurrentUser, User

router = APIRouter()


@router.get("/test-auth/", status_code=200)
def test_auth(user: CurrentUser) -> User:
    """
    Test Auth, returns the user.
    """
    return user
