from database.models_v1 import DerivedContent, DerivedContentType, Workspace
from pydantic import BaseModel
from sqlmodel import Session, asc, desc, select

from app.api.auth import CurrentUser
from app.core.logger import logger


class ListContentInput(BaseModel):
    text: str | None
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"
    status: str | None = None
    content_type_id: list[str] | None = None
    tags: list[str] | None = None


class ListContentResults(BaseModel):
    results: list[DerivedContent]
    offset: int
    limit: int


class ListContentTypesResults(BaseModel):
    results: list[DerivedContentType]


def list_content(session: Session, user: CurrentUser, input: ListContentInput):
    statement = (
        select(DerivedContent)
        .join(Workspace)
        .where(user.organization_id == Workspace.organization_id)
        # .join(Codebase)
        # .filter(
        #     or_(
        #         [
        #             user.organization_id == Codebase.workspace.organization_id,
        #             user.organization_id == Workspace.organization_id,
        #         ]
        #     )
        # )
        .offset(input.offset)
        .limit(input.limit)
    )
    if input.sort_by:
        if input.sort_direction == "ASC":
            statement = statement.order_by(asc(input.sort_by))
        elif input.sort_direction == "DESC":
            statement = statement.order_by(desc(input.sort_by))
        else:
            logger.error("Invalid sort direction provided.")
            raise RuntimeError(
                "Invalid sort direction provided. Options are ASC or DESC"
            )

    if input.text:
        statement = statement.where(DerivedContent.relative_path.contains(input.text))

    if input.status:
        statement = statement.where(DerivedContent.status == input.status)

    if input.content_type_id and len(input.content_type_id) > 0:
        statement = statement.where(
            DerivedContent.content_type_id.in_(input.content_type_id)
        )

    results = session.exec(statement).all()
    return ListContentResults(results=results, offset=input.offset, limit=input.limit)


def list_content_types(session: Session):
    results = session.exec(select(DerivedContentType)).all()
    return ListContentTypesResults(results=results)
