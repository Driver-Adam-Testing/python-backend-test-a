from database.models_v1 import DocumentSource
from database.models_v2 import Node, PrimaryAsset, Version
from fastapi import Request
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
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
