from database.db import get_session
from database.models import PrimaryAsset, Version
from database.models_enums import PrimaryAssetKind, VersionStatus
from sqlmodel import select

from shared.authorization.query_filters import primary_asset_grant_filter


def get_codebase_names(org_id: str, user_id: str) -> list[str]:
    """
    Get names of all codebases that have at least one completed version for a specific organization
    and that the user has access to.
    """
    with get_session() as db:
        assets = db.exec(
            select(PrimaryAsset.display_name)
            .join(Version, Version.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAsset.organization_id == org_id)
            .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
            .where(Version.status == VersionStatus.GENERATION_COMPLETE)
            .where(primary_asset_grant_filter(db, user_id, org_id))
            .distinct()
        ).all()

        return assets
