from uuid import UUID

from database.models_v2 import PrimaryAsset, PrimaryAssetTag
from fastapi import Body, HTTPException, Path, Response
from sqlmodel import select

from app.api.auth import UserToken
from app.api.routes.v2.router import router
from app.api.routes.v2.schemas import PrimaryAssetTagCreate
from app.api.session import CurrentSession


@router.delete("/primary_asset_tags/{primary_asset_id}/{tag_id}", response_model=None)
def delete_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    tag_id: UUID = Path(...),
    primary_asset_id: UUID = Path(...),
) -> Response:
    primary_asset_tag = session.exec(
        select(PrimaryAssetTag)
        .join(PrimaryAsset)
        .where(PrimaryAssetTag.tag_id == tag_id)
        .where(PrimaryAssetTag.primary_asset_id == primary_asset_id)
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).one_or_none()

    if not primary_asset_tag:
        raise HTTPException(
            status_code=404, detail="PrimaryAssetTag not found or not authorized"
        )

    session.delete(primary_asset_tag)
    session.commit()
    return Response(status_code=204)


@router.post("/primary_asset_tags", response_model=PrimaryAssetTag)
def create_primary_asset_tag(
    session: CurrentSession,
    user: UserToken,
    payload: PrimaryAssetTagCreate = Body(...),
) -> PrimaryAssetTag:
    new_primary_asset_tag = PrimaryAssetTag(
        tag_id=payload.tag_id,
        primary_asset_id=payload.primary_asset_id,
    )
    session.add(new_primary_asset_tag)
    session.commit()
    session.refresh(new_primary_asset_tag)
    return new_primary_asset_tag
