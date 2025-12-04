from uuid import UUID

from database.models import DocumentSource, PrimaryAsset, Version, VersionNode
from fastapi import HTTPException, Query, Request
from shared.authorization.query_filters import page_source_authorization_filter
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
from app.authorization.fastapi import enforce_asset_action


@router.get("/page_sources", response_model=ListWithCount[DocumentSourceDetailRead])
def list_page_sources(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    page_version_node_id: UUID = Query(..., description="Page node ID (required)"),
) -> ListWithCount[DocumentSourceRead]:
    """
    List sources for a specific page.

    Requires page_node_id parameter. User must have access to ALL sources
    for the page to view the page sources.
    """
    page_version_node = session.exec(
        select(VersionNode)
        .options(selectinload(VersionNode.version))
        .where(VersionNode.id == page_version_node_id)
    ).one_or_none()

    if not page_version_node:
        raise HTTPException(status_code=404, detail="Page version node not found")

    page_asset_id = page_version_node.version.primary_asset_id

    page_asset = session.exec(
        select(PrimaryAsset).where(PrimaryAsset.id == page_asset_id)
    ).one_or_none()

    if not page_asset or page_asset.organization_id != user.organization_id:
        raise HTTPException(status_code=404, detail="Page not found")

    page_query = (
        select(PrimaryAsset)
        .where(PrimaryAsset.id == page_asset_id)
        .where(
            page_source_authorization_filter(
                session, user.user_id, user.organization_id
            )
        )
    )

    authorized_page = session.exec(page_query).one_or_none()

    if not authorized_page:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You must have access to all sources for this page.",
        )

    if pagination.sort_by == "updated_at":
        pagination.sort_by = None

    query = (
        select(DocumentSource)
        .join(DocumentSource.page_version_node)
        .join(VersionNode.version)
        .join(Version.primary_asset)
        .options(
            selectinload(DocumentSource.source_version_node)
            .selectinload(VersionNode.version)
            .selectinload(Version.primary_asset),
        )
        .where(DocumentSource.page_version_node_id == page_version_node_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    filters = dict(request.query_params)

    print("HERE ARE THE FILTERS", filters)

    query = apply_filters_to_query(query, filters, DocumentSource)
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()

    query = apply_sorting_to_query(query, pagination, DocumentSource)
    result = session.exec(query)
    document_sources = result.all()

    return ListWithCount(results=document_sources, total_count=total_count)


@router.post("/document_sources/batch", response_model=list[DocumentSourceDetailRead])
def batch_create_document_sources(
    session: CurrentSession,
    user: UserToken,
    payload: list[DocumentSourceCreate],
) -> list[DocumentSourceDetailRead]:
    source_version_node_ids = {data.source_version_node_id for data in payload}
    query = (
        select(VersionNode)
        .where(VersionNode.id.in_(source_version_node_ids))
        .options(selectinload(VersionNode.version))
    )
    source_version_nodes = session.exec(query).all()

    for source_version_node in source_version_nodes:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=source_version_node.version.primary_asset_id,
            action_key="asset.use_as_source",
        )

    created_document_sources = []

    for data in payload:
        # Delete existing sources with the same page_version_node_id
        session.exec(
            delete(DocumentSource).where(
                DocumentSource.page_version_node_id == data.page_version_node_id
            )
        )

    # Create new DocumentSource instances
    new_document_sources = [
        DocumentSource(
            source_version_node_id=data.source_version_node_id,
            page_version_node_id=data.page_version_node_id,
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
    # NOTE: depending on how we implement the sources/generate flow for autodocs, this may be unneeded.
    # Because sources are supposed to be read-only once generation has commenced, it wouldn't be meaningful to delete sources.

    # Verify user has access to all source nodes before deleting; probably not strictly necessary,
    # but it makes the authz test coverage happy!
    source_version_node_ids = {data.source_version_node_id for data in payload}
    query = (
        select(VersionNode)
        .where(VersionNode.id.in_(source_version_node_ids))
        .options(selectinload(VersionNode.version))
    )
    source_version_nodes = session.exec(query).all()
    for source_version_node in source_version_nodes:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=source_version_node.version.primary_asset_id,
            action_key="asset.use_as_source",
        )

    deletion_results = []

    for data in payload:
        # Delete the document source with the specified source_node_id and page_node_id
        result = session.exec(
            delete(DocumentSource).where(
                DocumentSource.source_version_node_id == data.source_version_node_id,
                DocumentSource.page_version_node_id == data.page_version_node_id,
                PrimaryAsset.organization_id == user.organization_id,
            )
        )
        session.commit()

        # Append True if a row was deleted, otherwise False
        deletion_results.append(result.rowcount > 0)

    return deletion_results
