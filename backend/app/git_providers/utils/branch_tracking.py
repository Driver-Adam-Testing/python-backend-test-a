from database.models import PrimaryAsset
from database.models_enums import PrimaryAssetKind
from sqlmodel import Session, select


def get_tracked_branch_or_none(
    session: Session,
    org_id: str,
    repo_name: str,
) -> str | None:
    primary_asset = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            PrimaryAsset.display_name == repo_name,
            PrimaryAsset.kind == PrimaryAssetKind.CODEBASE,
        )
    ).one_or_none()
    if primary_asset is None:
        return None
    return primary_asset.vcs_tracked_branch
