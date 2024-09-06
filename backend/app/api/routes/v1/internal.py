from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.auth import CurrentToken
from app.api.session import CurrentSession
from app.core.config import settings
from app.core.logger import logger
from app.schemas.content_schema import (
    ListContentInput,
    ListContentResults,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.get(
    "/{organization_id}/content",
    summary="List content matching the provided filter criteria",
)
def list_content(
    session: CurrentSession,
    current_token: CurrentToken,
    organization_id: str,
    limit: int | None = 20,
    offset: int | None = 0,
    content_type_id: Annotated[list[str] | None, Query()] = None,
    content_type_name: Annotated[list[str] | None, Query()] = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    tag: Annotated[list[str] | None, Query()] = None,
    tag_id: Annotated[list[str] | None, Query()] = None,
    text: str | None = None,
) -> ListContentResults:
    """
    List content matching the provided filter criteria.

    This endpoint is intended for internal use and requires a machine-to-machine (M2M) token
    with the appropriate audience.

    Args:
        session (CurrentSession): The current session.
        current_token (CurrentToken): The current authentication token.
        organization_id (str): The ID of the organization.
        limit (int, optional): The maximum number of items to return. Defaults to 20.
        offset (int, optional): The number of items to skip before starting to collect the result set. Defaults to 0.
        content_type_id (list[str], optional): List of content type IDs to filter by.
        content_type_name (list[str], optional): List of content type names to filter by.
        sort_by (str, optional): The field to sort by.
        sort_direction (str, optional): The direction to sort by. Defaults to "ASC".
        status (str, optional): The status to filter by.
        tag (list[str], optional): List of tags to filter by.
        tag_id (list[str], optional): List of tag IDs to filter by.
        text (str, optional): Text to search for in the content.

    Returns:
        ListContentResults: The results of the content list query.

    Raises:
        HTTPException: If the token does not have the required permissions or is unauthorized.
    """
    # Authorization check
    if current_token is None or current_token.audience != settings.AUTH0_AUDIENCE:
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(
        f"Listing content for organization_id: {organization_id} with limit: {limit}, offset: {offset}"
    )

    content_service = ContentService(session)
    results = content_service.get_list_content(
        organization_id,
        ListContentInput(
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            content_type_name=content_type_name,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
            tags=tag,
            tag_ids=tag_id,
        ),
    )
    return results
