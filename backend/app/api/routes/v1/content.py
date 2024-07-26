from typing import Annotated

from fastapi import APIRouter, Query

from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from app.utils.content import (
    ListContentInput,
    ListContentResults,
    ListContentTypesResults,
    list_content,
    list_content_types,
)

router = APIRouter()


@router.get(
    "/",
    summary="List content matching the provided filter criteria",
)
def list(
    session: CurrentSession,
    user: CurrentUser,
    limit: int | None = 20,
    text: str | None = None,
    offset: int | None = 0,
    content_type_id: Annotated[list[str], Query()] | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = "ASC",
    status: str | None = None,
    tags: Annotated[list[str], Query()] | None = None,
) -> ListContentResults:
    return list_content(
        session,
        user,
        ListContentInput(
            limit=limit,
            offset=offset,
            text=text,
            content_type_id=content_type_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
            status=status,
            tags=tags,
        ),
    )


@router.get(
    "/types",
    summary="List content types",
)
def list_types(session: CurrentSession, user: CurrentUser) -> ListContentTypesResults:
    return list_content_types(session)
