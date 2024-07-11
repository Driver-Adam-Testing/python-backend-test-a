from fastapi import APIRouter

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.utils.search import SearchInput, SearchResults, search_content_metadata

router = APIRouter()


@router.post(
    "/",
    summary="Search for content",
    response_description="Return HTTP Status Code 200 (OK)",
)
def search(
    session: CurrentSession, user: CurrentUser, input: SearchInput
) -> SearchResults:
    try:
        organization_id = user.organization_id
    except Exception:
        organization_id = None
    return search_content_metadata(
        session=session, organization_id=organization_id, input=input
    )
