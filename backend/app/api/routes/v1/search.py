from fastapi import APIRouter
from shared.pipelines.search import SearchInput, SearchResults, search_content_metadata

from app.api.auth import CurrentToken
from app.api.session import CurrentSession

router = APIRouter()


@router.post(
    "/",
    summary="Search for content",
    response_description="Return HTTP Status Code 200 (OK)",
)
def search(
    session: CurrentSession, m2m: CurrentToken, input: SearchInput
) -> SearchResults:
    return search_content_metadata(session=session, organization_id=None, input=input)
