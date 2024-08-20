from fastapi import APIRouter
from shared.interfaces.search import SearchInput, SearchResults
from shared.pipelines.search import search_content

from app.api.auth import CurrentUser
from app.api.session import CurrentSession

router = APIRouter()


@router.post(
    "/",
    summary="Search for content",
    response_description="Return Search Results",
)
def search(
    session: CurrentSession, user: CurrentUser, input: SearchInput
) -> SearchResults:
    # TODO: figure out how to do this without transforming the input.

    input.organization_id = user.organization_id
    return search_content(session=session, input=input)
