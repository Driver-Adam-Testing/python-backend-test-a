from database.models import Message
from fastapi import APIRouter
from pydantic.networks import EmailStr

from app.api.auth import CurrentUser, User
from app.utils import generate_test_email, send_email

router = APIRouter()


@router.post(
    "/test-email/",
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/test-auth/", status_code=200)
def test_auth(user: CurrentUser) -> User:
    """
    Test Auth, returns the user.
    """
    return user
