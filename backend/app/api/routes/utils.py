from database.models import Message
from fastapi import APIRouter, Depends, Security
from pydantic.networks import EmailStr

from app.api.auth import Auth0User, auth
from app.api.deps import get_current_active_superuser
from app.utils import generate_test_email, send_email

router = APIRouter()


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
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


@router.get(
    "/test-auth/", dependencies=[Depends(auth.authcode_scheme)], status_code=200
)
def test_auth(user: Auth0User = Security(auth.get_user)) -> None:
    """
    Test Auth.
    """
    print(user)
    return None
