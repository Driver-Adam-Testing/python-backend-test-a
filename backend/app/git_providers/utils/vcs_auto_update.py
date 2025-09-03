from datetime import UTC, datetime
from uuid import UUID

from database.models import PrimaryAsset, PrimaryAssetKind, VcsAutoUpdatePolicy, Version
from sqlmodel import Session, select


def _get_codebase_asset(
    session: Session, org_id: str, repo_name: str
) -> PrimaryAsset | None:
    primary_asset = session.exec(
        select(PrimaryAsset).where(
            PrimaryAsset.organization_id == org_id,
            PrimaryAsset.display_name == repo_name,
            PrimaryAsset.kind == PrimaryAssetKind.CODEBASE,
        )
    ).one_or_none()
    return primary_asset


def _seconds_since_version_created(
    version: Version,
) -> int:
    push_timestamp = datetime.now(UTC)
    return int((push_timestamp - version.created_at).total_seconds())


def _get_latest_version(session: Session, primary_asset_id: UUID) -> Version | None:
    latest_version = session.exec(
        select(Version)
        .where(Version.primary_asset_id == primary_asset_id)
        .order_by(Version.created_at.desc())
    ).first()
    return latest_version


def is_update_required(
    session: Session,
    org_id: str,
    repo_name: str,
) -> tuple[bool, dict[str, str]]:
    codebase_primary_asset = _get_codebase_asset(
        session=session, org_id=org_id, repo_name=repo_name
    )

    if not codebase_primary_asset:
        return (
            False,
            {
                "message": f"Codebase primary asset record not found for repo: {repo_name}"
            },
        )

    match codebase_primary_asset.vcs_auto_update_policy:
        case VcsAutoUpdatePolicy.NEVER:
            return (
                False,
                {"message": "Push event ignored (updates are disabled)"},
            )

        case VcsAutoUpdatePolicy.AFTER_EVERY_COMMIT:
            pass
        case (
            VcsAutoUpdatePolicy.AFTER_ONE_DAY_OR_MORE
            | VcsAutoUpdatePolicy.AFTER_THREE_DAYS_OR_MORE
            | VcsAutoUpdatePolicy.AFTER_ONE_WEEK_OR_MORE
            | VcsAutoUpdatePolicy.AFTER_TWO_WEEKS_OR_MORE
            | VcsAutoUpdatePolicy.AFTER_FOUR_WEEKS_OR_MORE
        ):
            latest_version = _get_latest_version(
                session=session, primary_asset_id=codebase_primary_asset.id
            )
            if not latest_version:
                pass
            elif (
                _seconds_since_version_created(version=latest_version)
                < VcsAutoUpdatePolicy(
                    codebase_primary_asset.vcs_auto_update_policy
                ).to_seconds()
            ):
                return (
                    False,
                    {
                        "message": f"Push event ignored (new push has not occurred {codebase_primary_asset.vcs_auto_update_policy} since the previous update)"
                    },
                )

        case _:
            return (
                False,
                {"message": "Push event ignored (not a valid policy)"},
            )

    return (
        True,
        {"message": "Push event processed"},
    )
