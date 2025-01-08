from uuid import UUID

from database.models_v1 import DocumentSource
from database.models_v2 import Node, PrimaryAsset, Version
from fastapi import Request
from sqlalchemy.orm import selectinload
from sqlmodel import delete, func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
    DocumentSourceCreate,
    DocumentSourceDetailRead,
    DocumentSourceRead,
    ListWithCount,
)
from app.api.session import CurrentSession


@router.get("/document_sources", response_model=ListWithCount[DocumentSourceDetailRead])
async def list_document_sources(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
) -> ListWithCount[DocumentSourceRead]:
    if pagination.sort_by == "updated_at":
        pagination.sort_by = None
    query = (
        select(DocumentSource)
        .join(DocumentSource.source_node)
        .join(Node.version)
        .join(Version.primary_asset)
        .options(
            selectinload(DocumentSource.source_node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
        )
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, DocumentSource)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, DocumentSource)
    result = session.exec(query)
    document_sources = result.all()

    return ListWithCount(results=document_sources, total_count=total_count)


@router.post("/document_sources", response_model=DocumentSourceDetailRead)
async def create_document_source(
    session: CurrentSession,
    user: UserToken,
    payload: DocumentSourceCreate,
) -> DocumentSourceDetailRead:
    # Create a new DocumentSource instance
    new_document_source = DocumentSource(
        source_node_id=payload.source_node_id,
        page_node_id=payload.page_node_id,
    )

    # Add the new document source to the session
    session.add(new_document_source)
    session.commit()

    # Refresh the session to get the updated document source
    session.refresh(new_document_source)

    return new_document_source


@router.delete("/document_sources/{page_node_id}/{source_node_id}", response_model=bool)
async def delete_document_source(
    session: CurrentSession,
    user: UserToken,
    page_node_id: UUID,
    source_node_id: UUID,
) -> bool:
    # Delete the document source with the specified source_node_id and page_node_id
    result = session.exec(
        delete(DocumentSource).where(
            DocumentSource.source_node_id == source_node_id,
            DocumentSource.page_node_id == page_node_id,
            PrimaryAsset.organization_id == user.organization_id,
        )
    )
    session.commit()

    # Return True if a row was deleted, otherwise False
    return result.rowcount > 0


@router.post("/document_sources/batch", response_model=list[DocumentSourceDetailRead])
async def batch_create_document_sources(
    session: CurrentSession,
    user: UserToken,
    payload: list[DocumentSourceCreate],
) -> list[DocumentSourceDetailRead]:
    created_document_sources = []

    for data in payload:
        # Delete existing sources with the same page_node_id
        session.exec(
            delete(DocumentSource).where(
                DocumentSource.page_node_id == data.page_node_id
            )
        )

    # Create new DocumentSource instances
    new_document_sources = [
        DocumentSource(
            source_node_id=data.source_node_id,
            page_node_id=data.page_node_id,
        )
        for data in payload
    ]

    # Add the new document sources to the session
    session.add_all(new_document_sources)
    session.commit()

    # Refresh the session to get the updated document sources
    for new_document_source in new_document_sources:
        session.refresh(new_document_source)
        created_document_sources.append(new_document_source)

    return created_document_sources


@router.delete("/document_sources/batch", response_model=list[bool])
async def batch_delete_document_sources(
    session: CurrentSession,
    user: UserToken,
    payload: list[DocumentSourceCreate],
) -> list[bool]:
    deletion_results = []

    for data in payload:
        # Delete the document source with the specified source_node_id and page_node_id
        result = session.exec(
            delete(DocumentSource).where(
                DocumentSource.source_node_id == data.source_node_id,
                DocumentSource.page_node_id == data.page_node_id,
                PrimaryAsset.organization_id == user.organization_id,
            )
        )
        session.commit()

        # Append True if a row was deleted, otherwise False
        deletion_results.append(result.rowcount > 0)

    return deletion_results
