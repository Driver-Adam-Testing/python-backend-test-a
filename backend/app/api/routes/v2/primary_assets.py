import hashlib
from logging import getLogger
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from database.models import (
    DerivedContent,
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
from app.core.config import settings  # Assuming settings contains AWS credentials

logger = getLogger(__name__)


@router.get("/primary_assets", response_model=ListWithCount[PrimaryAssetDetailRead])
def list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    tag_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    return _list_primary_assets(request, session, user, pagination, tag_ids)


def _list_primary_assets(
    request: Request,
    session: CurrentSession,
    user: User,
    pagination: Pagination,
    tag_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    query = (
        select(PrimaryAsset)
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

    filters = dict(request.query_params)
    query = apply_filters_to_query(query, filters, PrimaryAsset)

    if tag_ids:
        query = query.where(
            select(PrimaryAssetTag)
            .where(PrimaryAssetTag.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAssetTag.tag_id.in_(tag_ids.split(",")))
            .exists()
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    # TODO: This is a hack to sort by total_files. We should use the query utils instead, but It's very problematic.
    if pagination.sort_by == "most_recent_version.root_node.total_files":
        primary_assets = session.exec(query).all()
        primary_assets = sorted(
            primary_assets,
            key=lambda x: (
                x.most_recent_version.root_node.total_files
                if x.most_recent_version.root_node
                else 0
            ),
            reverse=(pagination.sort_direction == "DESC"),
        )
        primary_assets = primary_assets[
            pagination.offset : pagination.offset + pagination.limit
        ]
    else:
        query = apply_sorting_to_query(query, pagination, PrimaryAsset)
        result = session.exec(query)
        primary_assets = result.all()

    return ListWithCount(results=primary_assets, total_count=total_count)


@router.put("/primary_assets/{primary_asset_id}", response_model=PrimaryAsset)
def update_primary_asset(
    session: CurrentSession,
    user: UserToken,
    primary_asset_id: UUID = Path(...),
    payload: PrimaryAssetUpdate = Body(...),
) -> PrimaryAsset:
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
