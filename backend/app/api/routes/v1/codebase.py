from datetime import datetime
from uuid import UUID

from database.models_v2 import PrimaryAssetRow, VersionRow
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import func, select

from app.api.auth import ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession

router = APIRouter()


class VersionResponse(BaseModel):
    id: UUID
    version: str
    display_name: str | None
    created_at: datetime


class CodebaseVersionsResponse(BaseModel):
    versions: list[VersionResponse]
    total_count: int
    limit: int
    offset: int


@router.get(
    "/{codebase_id}/versions",
    summary="Get available codebase versions",
    dependencies=[ContentReadonlyPermission],
)
def get_codebase_versions(
    session: CurrentSession,
    user: UserToken,
    codebase_id: UUID,
    limit: int = Query(default=10, gt=0),
    offset: int = Query(default=0, ge=0),
) -> CodebaseVersionsResponse:
    # Find the primary asset that represents the codebase
    primary_asset = session.exec(
        select(PrimaryAssetRow).where(
            PrimaryAssetRow.id == codebase_id,
            PrimaryAssetRow.organization_id == user.organization_id,
            PrimaryAssetRow.primary_asset_type
            == "CODEBASE",  # Ensuring it's a codebase
        )
    ).one_or_none()

    if not primary_asset:
        # If not found, raise an error
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Codebase not found")

    # Query versions associated with this primary asset
    statement = (
        select(VersionRow)
        .where(VersionRow.primary_asset_id == primary_asset.id)
        .order_by(VersionRow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    versions = session.exec(statement).all()

    # Count total number of versions for pagination
    total_count = session.exec(
        select(func.count(VersionRow.id)).where(
            VersionRow.primary_asset_id == primary_asset.id
        )
    ).one()

    response_data = [
        VersionResponse(
            id=version.id,
            # Here we treat the version's display_name as the "version" string
            version=version.display_name,
            display_name=version.display_name,
            created_at=version.created_at if version.created_at else datetime.now(),
        )
        for version in versions
    ]

    return CodebaseVersionsResponse(
        versions=response_data, total_count=total_count, limit=limit, offset=offset
    )
