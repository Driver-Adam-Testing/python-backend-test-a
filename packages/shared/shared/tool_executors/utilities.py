from database.models import PrimaryAsset, Version
from database.models_enums import PrimaryAssetKind, VersionStatus
from sqlmodel import Session, select

from shared.authorization.query_filters import primary_asset_grant_filter


def get_latest_version_for_codebase(
    db: Session, org_id: str, codebase_name: str, user_id: str
) -> Version | None:
    return db.exec(
        select(Version)
        .join(PrimaryAsset, PrimaryAsset.id == Version.primary_asset_id)
        .where(PrimaryAsset.display_name == codebase_name)
        .where(PrimaryAsset.organization_id == org_id)
        .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        .where(Version.status == VersionStatus.GENERATION_COMPLETE)
        .where(primary_asset_grant_filter(db, user_id, org_id))
        .order_by(Version.updated_at.desc())
    ).first()
