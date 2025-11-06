import hashlib
from logging import getLogger
from typing import Any
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from database.models import (
    DerivedContent,
    DocumentSource,
    InspectorRun,
    Node,
    PrimaryAsset,
    PrimaryAssetTag,
    Version,
)
from database.models_enums import (
    ContentKind,
)
from fastapi import Body, HTTPException, Path, Request
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlmodel import func, select

from app.api.auth import UserToken
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import (
    ListWithCount,
    PrimaryAssetDetailRead,
    PrimaryAssetUpdate,
)
from app.api.session import CurrentSession
from app.auth.models import User
from app.authorization.fastapi import enforce_asset_action
from app.authorization.query_filters import (
    effective_asset_role_expr,
    exclude_page_assets_filter,
    page_asset_grant_filter,
    primary_asset_grant_filter,
)
from app.core.config import settings  # Assuming settings contains AWS credentials

logger = getLogger(__name__)


@router.get("/primary_assets", response_model=ListWithCount[PrimaryAssetDetailRead])
def list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    tag_ids: str | None = None,
    document_source_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    """
    List non-page primary assets (CODEBASE, FILE, etc).

    Uses standard asset-based authorization. For PAGE assets, use /page_assets.
    """
    return _list_assets_with_filter(
        request,
        session,
        user,
        pagination,
        auth_filter=lambda s, uid, oid: primary_asset_grant_filter(s, uid, oid),
        asset_kind_filter=exclude_page_assets_filter(),
        tag_ids=tag_ids,
        document_source_ids=document_source_ids,
    )


@router.get("/page_assets", response_model=ListWithCount[PrimaryAssetDetailRead])
def list_page_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    tag_ids: str | None = None,
    document_source_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    """
    List PAGE assets where user has grants to ALL sources.

    This endpoint only returns PAGE and PAGE_TEMPLATE assets.
    Authorization is source-based: user must have access to ALL sources
    referenced by each page.
    """
    return _list_assets_with_filter(
        request,
        session,
        user,
        pagination,
        auth_filter=lambda s, uid, oid: page_asset_grant_filter(s, uid, oid),
        asset_kind_filter=None,  # page_asset_grant_filter already includes kind filter
        tag_ids=tag_ids,
        document_source_ids=document_source_ids,
    )


def _list_assets_with_filter(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    auth_filter: callable,
    asset_kind_filter: Any | None = None,
    tag_ids: str | None = None,
    document_source_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    role_expr = effective_asset_role_expr(
        session, user.user_id, user.organization_id, PrimaryAsset.id
    )
    query = (
        select(PrimaryAsset, role_expr.label("effective_role"))
        .options(
            selectinload(PrimaryAsset.most_recent_version),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.root_node
            ),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.creator
            ),
            selectinload(PrimaryAsset.most_recent_version)
            .selectinload(Version.root_node)
            .selectinload(Node.contents),
            selectinload(PrimaryAsset.most_recent_completed_version),
            selectinload(PrimaryAsset.most_recent_completed_version).selectinload(
                Version.root_node
            ),
            selectinload(PrimaryAsset.most_recent_completed_version).selectinload(
                Version.creator
            ),
            selectinload(PrimaryAsset.most_recent_completed_version)
            .selectinload(Version.root_node)
            .selectinload(Node.contents),
            with_loader_criteria(
                DerivedContent,
                DerivedContent.content_kind == ContentKind.TOP_LEVEL_TERSE_SENTENCE,
            ),
        )
        .where(PrimaryAsset.organization_id == user.organization_id)
    )

    if asset_kind_filter is not None:
        query = query.where(asset_kind_filter)

    query = query.where(auth_filter(session, user.user_id, user.organization_id))

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, PrimaryAsset)

    if tag_ids:
        query = query.where(
            select(PrimaryAssetTag)
            .where(PrimaryAssetTag.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAssetTag.tag_id.in_(tag_ids.split(",")))
            .exists()
        )

    if document_source_ids:
        """
        TODO: Complex logic with inline comments should be extracted to well-named functions
        """
        source_primary_asset_ids = document_source_ids.split(",")

        # Need to use aliases to join through both page_node and source_node
        from sqlalchemy import alias

        SourceNode = alias(Node, name="source_node")
        SourceVersion = alias(Version, name="source_version")

        query = query.where(
            select(DocumentSource)
            .join(DocumentSource.page_node)  # Join to the page's node
            .join(Node.version)  # Join to the page's version
            .where(
                Version.primary_asset_id == PrimaryAsset.id
            )  # Link to outer query PrimaryAsset (the page)
            .join(
                SourceNode, DocumentSource.source_node_id == SourceNode.c.id
            )  # Join to source node
            .join(
                SourceVersion, SourceNode.c.version_id == SourceVersion.c.id
            )  # Join to source version
            .where(
                SourceVersion.c.primary_asset_id.in_(source_primary_asset_ids)
            )  # Filter by source codebases
            .exists()
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    # TODO: This is a hack to sort by total_files. We should use the query utils instead, but It's very problematic.
    if pagination.sort_by == "most_recent_version.root_node.total_files":
        results = session.exec(query).all()
        results = sorted(
            results,
            key=lambda row: (
                row[0].most_recent_version.root_node.total_files
                if row[0].most_recent_version.root_node
                else 0
            ),
            reverse=(pagination.sort_direction == "DESC"),
        )
        results = results[pagination.offset : pagination.offset + pagination.limit]
    else:
        query = apply_sorting_to_query(query, pagination, PrimaryAsset)
        results = session.exec(query).all()

    # This is awkward: we need to add effective_role to each asset, but can't do it directly
    # because PrimaryAsset is a SQLModel and Pydantic models are immutable. Using **asset.__dict__
    # is gross because it includes SQLAlchemy internals, but model_construct() filters to only
    # defined fields so it's safe. This is a symptom of endpoints being tightly coupled to table
    # definitions rather than serving the needs of the application
    primary_assets: list[PrimaryAssetDetailRead] = []
    for asset, role in results:
        asset_with_role = PrimaryAssetDetailRead.model_construct(
            **asset.__dict__,
            effective_role=role,
        )
        primary_assets.append(asset_with_role)

    return ListWithCount(results=primary_assets, total_count=total_count)


@router.put("/primary_assets/{primary_asset_id}", response_model=PrimaryAsset)
def update_primary_asset(
    session: CurrentSession,
    user: UserToken,
    primary_asset_id: UUID = Path(...),
    payload: PrimaryAssetUpdate = Body(...),
) -> PrimaryAsset:
    enforce_asset_action(
        db=session, user=user, asset_id=primary_asset_id, action_key="asset.manage"
    )
    asset = session.exec(
        select(PrimaryAsset)
        .where(PrimaryAsset.id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    if payload.display_name is not None:
        asset.display_name = payload.display_name
    if payload.codebase_settings_auto_commit_docs is not None:
        asset.codebase_settings_auto_commit_docs = (
            payload.codebase_settings_auto_commit_docs
        )
    if payload.vcs_auto_update_policy is not None:
        asset.vcs_auto_update_policy = payload.vcs_auto_update_policy

    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


@router.delete("/primary_assets/{primary_asset_id}", response_model=PrimaryAsset)
def delete_primary_asset(
    session: CurrentSession,
    user: UserToken,
    primary_asset_id: UUID = Path(...),
) -> PrimaryAsset:
    enforce_asset_action(
        db=session, user=user, asset_id=primary_asset_id, action_key="asset.delete"
    )
    asset = session.exec(
        select(PrimaryAsset)
        .where(PrimaryAsset.id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Primary asset not found")

    run_ids = session.exec(
        select(InspectorRun.id)
        .join(Version)
        .where(Version.primary_asset_id == asset.id)
    ).all()

    org_id_hash = hashlib.sha256(user.organization_id.encode()).hexdigest()[:63]
    prefix = f"{primary_asset_id}/"

    s3 = boto3.resource(
        "s3",
        aws_access_key_id=settings.S3ADMIN_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3ADMIN_AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    bucket = s3.Bucket(org_id_hash)
    inspector_bucket = s3.Bucket(settings.INSPECTOR_BUCKET_NAME)

    try:
        bucket.objects.filter(Prefix=prefix).delete()
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucket":
            logger.warning(
                f"Bucket {org_id_hash} for {user.organization_id} does not exist. Still deleting asset from DB."
            )
        else:
            raise

    for run_id in run_ids:
        inspector_bucket.objects.filter(Prefix=str(run_id)).delete()
        # TODO: instead of storing run data in a separate bucket, place in the org bucket under the primary asset

    session.delete(asset)
    session.commit()

    return asset
