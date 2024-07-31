from datetime import datetime
from typing import Optional
from uuid import UUID

from database.models_v1 import (
    DerivedContent,
    DerivedContentType,
    Enum_Derived_Content_Status,
    Tag,
    TagContent,
    Workspace,
)
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, asc, desc, or_, select

from app.api.auth import CurrentUser
from app.core.logger import logger


class ListContentInput(BaseModel):
    text: str | None = None
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"
    status: str | None = None
    content_type_id: list[str] | None = None
    tags: list[str] | None = None
    tag_ids: list[str] | None = None
    workspace_id: str | None = None


class ListContentTypesInput(BaseModel):
    limit: int | None = 20
    offset: int | None = 0
    sort_by: str | None = None
    sort_direction: str | None = "DESC"


class ListContentTypesResults(BaseModel):
    results: list[DerivedContentType]


class ListContentResult(BaseModel):
    id: UUID
    content_type_id: UUID
    content_type: DerivedContentType
    # All content must be in a workspace
    workspace_id: UUID
    workspace_name: str
    source_content_id: UUID | None
    # Content doesn't need to be associated with a codebase in our flat asset design
    codebase_id: None | UUID
    relative_path: str
    content: None | str
    misc_metadata: dict | None
    status: Enum_Derived_Content_Status | None
    tags: list[Tag]
    created_at: None | datetime
    updated_at: None | datetime
    source_content: Optional["DerivedContent"]
    order: int | None


class ListContentResults(BaseModel):
    results: list[ListContentResult]
    offset: int
    limit: int
    count: int


class TagAssociationResponse(BaseModel):
    tag_id: str
    content_id: str
    message: str


def list_content(
    session: Session, user: CurrentUser, input: ListContentInput
) -> ListContentResults:
    statement = (
        select(DerivedContent)
        .join(Workspace)
        .join(TagContent, isouter=True)
        .join(Tag, isouter=True)
        .where(user.organization_id == Workspace.organization_id)
    )
    count_statement = (
        select(func.count())
        .select_from(DerivedContent)
        .join(Workspace)
        .join(TagContent, isouter=True)
        .join(Tag, isouter=True)
        .where(user.organization_id == Workspace.organization_id)
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

    if input.workspace_id:
        statement = statement.where(DerivedContent.workspace_id == input.workspace_id)
        count_statement = count_statement.where(
            DerivedContent.workspace_id == input.workspace_id
        )

    if input.text:
        statement = statement.where(DerivedContent.relative_path.contains(input.text))
        count_statement = count_statement.where(
            DerivedContent.relative_path.contains(input.text)
        )

    if input.status:
        statement = statement.where(DerivedContent.status == input.status)
        count_statement = count_statement.where(DerivedContent.status == input.status)

    if input.content_type_id:
        statement = statement.where(
            DerivedContent.content_type_id.in_(input.content_type_id)
        )
        count_statement = count_statement.where(
            DerivedContent.content_type_id.in_(input.content_type_id)
        )

    if input.tags:
        tag_clauses = []
        for tag in input.tags:
            tag_clauses.append(Tag.name.contains(tag))
        statement = statement.where(or_(*tag_clauses))
        count_statement = count_statement.where(or_(*tag_clauses))

    if input.tag_ids:
        tag_id_clauses = []
        for tag_id in input.tag_ids:
            tag_id_clauses.append(Tag.id == tag_id)
        statement = statement.where(or_(*tag_id_clauses))
        count_statement = count_statement.where(or_(*tag_id_clauses))

    total_count = session.exec(count_statement).one()
    results = session.exec(statement.offset(input.offset).limit(input.limit)).all()
    return ListContentResults(
        results=(
            ListContentResult(
                id=result.id,
                content_type_id=result.content_type_id,
                content_type=result.content_type,
                workspace_id=result.workspace_id,
                workspace_name=result.workspace.display_name,
                source_content_id=result.source_content_id,
                codebase_id=result.codebase_id,
                relative_path=result.relative_path,
                content=result.content,
                misc_metadata=result.misc_metadata,
                status=result.status,
                created_at=result.created_at,
                updated_at=result.updated_at,
                source_content=result.source_content,
                order=result.order,
                tags=result.tags,
            )
            for result in results
        ),
        offset=input.offset,
        limit=input.limit,
        count=total_count,
    )


def list_content_types(session: Session, input: ListContentTypesInput):
    statement = select(DerivedContentType).offset(input.offset).limit(input.limit)
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
    results = session.exec(statement).all()
    return ListContentTypesResults(results=results)


def associate_tag(
    session: Session, user: CurrentUser, content_id: str, tag_id: str
) -> TagAssociationResponse:
    # Check if content exists
    content = session.exec(
        select(DerivedContent)
        .join(Workspace)
        .where(user.organization_id == Workspace.organization_id)
        .where(DerivedContent.id == content_id)
    ).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Check if tag exists
    tag = session.exec(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(user.organization_id == Tag.organization_id)
    ).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    # Associate tag with content
    content.tags.append(tag)
    session.commit()
    return TagAssociationResponse(
        tag_id=tag_id, content_id=content_id, message="Tag associated successfully"
    )


def disassociate_tag(
    session: Session, user: CurrentUser, content_id: str, tag_id: str
) -> TagAssociationResponse:
    # Check if content exists
    content = session.exec(
        select(DerivedContent)
        .join(Workspace)
        .join(DerivedContent.tags)
        .where(user.organization_id == Workspace.organization_id)
        .where(DerivedContent.id == content_id)
    ).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )

    # Check if tag exists
    tag = session.exec(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(user.organization_id == Tag.organization_id)
    ).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    # Disassociate tag with content
    link = session.exec(
        select(TagContent)
        .where(TagContent.tag_id == tag_id)
        .where(TagContent.content_id == content_id)
    ).first()
    if link:
        session.delete(link)
        session.commit()
        return TagAssociationResponse(
            tag_id=tag_id,
            content_id=content_id,
            message="Tag disassociated successfully",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tag association not found"
        )
