from database.db import get_session
from database.models import (
    DerivedContent,
    Node,
    PrimaryAsset,
    Version,
)
from database.models_enums import ContentKind, PrimaryAssetKind, VersionStatus
from sqlmodel import select

from shared.authorization.helpers import is_super_admin
from shared.authorization.query_filters import primary_asset_grant_filter

from .tool_use_error import ToolUseError


def _get_root_node_content(
    org_id: str, codebase_name: str, content_kind: ContentKind, user_id: str
) -> DerivedContent:
    with get_session() as db:
        primary_asset = db.exec(
            select(PrimaryAsset)
            .where(PrimaryAsset.display_name == codebase_name)
            .where(PrimaryAsset.organization_id == org_id)
            .where(PrimaryAsset.kind == PrimaryAssetKind.CODEBASE)
        ).first()

        if not primary_asset:
            raise ToolUseError(
                agent_message=f"`{codebase_name}` is not a recognized codebase."
            )

        # Check authorization
        if not is_super_admin(db, user_id, org_id):
            has_grant = db.exec(
                select(PrimaryAsset)
                .where(PrimaryAsset.id == primary_asset.id)
                .where(PrimaryAsset.organization_id == org_id)
                .where(primary_asset_grant_filter(db, user_id, org_id))
            ).first()

            if not has_grant:
                raise ToolUseError(
                    agent_message=f"`{codebase_name}` is not a recognized codebase."
                )

        derived_content = db.exec(
            select(DerivedContent)
            .join(Node, Node.id == DerivedContent.node_id)
            .join(Version, Version.id == Node.version_id)
            .where(Version.primary_asset_id == primary_asset.id)
            .where(Version.status == VersionStatus.GENERATION_COMPLETE)
            .where(Node.depth == 0)
            .where(DerivedContent.content_kind == content_kind)
            .order_by(Version.updated_at.desc())
        ).first()

        if not derived_content:
            raise ToolUseError(
                agent_message=f"No {content_kind.value} content exists for the `{codebase_name}` codebase."
            )

        return derived_content


def get_architecture_overview(org_id: str, codebase_name: str, user_id: str) -> str:
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_ARCHITECTURE, user_id
    )
    return dc.content


def get_llm_onboarding_guide(org_id: str, codebase_name: str, user_id: str) -> str:
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_LLM_ONBOARDING, user_id
    )
    return dc.content


def get_changelog(org_id: str, codebase_name: str, user_id: str) -> str:
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_CHANGELOG, user_id
    )
    return dc.content or str(dc.misc_metadata)


def get_detailed_changelog(
    org_id: str, codebase_name: str, year: str, month: str, user_id: str
) -> str:
    dc = _get_root_node_content(
        org_id, codebase_name, ContentKind.DEEP_CONTEXT_CHANGELOG, user_id
    )
    return dc.misc_metadata.get(
        f"{year}-{month}", "No detailed changelog available for this month."
    )
