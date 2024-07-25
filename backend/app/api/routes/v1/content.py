from fastapi import APIRouter

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.utils.content import ListContentResults, list_content

router = APIRouter()


@router.get(
    "/",
    summary="List content matching the provided filter criteria",
    response_description="Return HTTP Status Code 200 (OK)",
)
def list(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    text: str | None = None,
    offset: int | None = 0,
    content_type: list[str] | None = None,
    # sort: "ASC" | "DESC" | None = None TODO - grouped sorting on the server gets complicated too
    # date: TODO - format? single date? date ranges? > date?
    labels: list[str] | None = None,
) -> ListContentResults:
    return list_content(session, user, input)
