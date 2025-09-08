from database.models import PrimaryAsset, Version
from database.models_enums import PrimaryAssetKind, VersionStatus
from sqlmodel import Session, select


def get_latest_version_for_codebase(
    db: Session, org_id: str, codebase_name: str
) -> Version | None:
    return db.exec(
        select(Version)
        .join(PrimaryAsset, PrimaryAsset.id == Version.primary_asset_id)
        .where(PrimaryAsset.display_name == codebase_name)
        .where(PrimaryAsset.organization_id == org_id)
        .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        .where(Version.status == VersionStatus.GENERATION_COMPLETE)
        .order_by(Version.updated_at.desc())
    ).first()
