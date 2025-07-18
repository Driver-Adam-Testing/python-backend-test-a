"""
app/api/routes/v2/codebase_cards.py
-----------------------------------

Return “CodebaseCards” with rich metadata and content classification.

Optimised version - minimises database round-trips while preserving
exactly the same read logic and response model.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any
from uuid import UUID  # noqa: TCH003

from database.models_v1 import DerivedContent
from database.models_v2 import (
    Node,
    PrimaryAsset,
    PrimaryAssetKind,
    PrimaryAssetProvider,
    Version,
)
from database.models_v2_enums import ContentKind, VersionStatus
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import func, or_
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import select

from app.api.auth import UserToken  # noqa: TCH001
from app.api.routes.v2.query_utils import Pagination  # noqa: TCH001
from app.api.routes.v2.schemas import ListWithCount, TagRead
from app.api.session import CurrentSession  # noqa: TCH001

# --------------------------------------------------------------------------------------
# Pydantic response models (unchanged)
# --------------------------------------------------------------------------------------


class CommitAuthor(BaseModel):
    name: str | None = None
    email: str | None = None
    date: datetime


class CommitInfo(BaseModel):
    sha: str | None = None
    short_sha: str | None = None
    message: str | None = None
    url: HttpUrl | None = None
    author: CommitAuthor


class BranchInfo(BaseModel):
    name: str
    protected: bool = False


class RepositoryInfo(BaseModel):
    name: str
    namespace: str | None = None
    full_name: str
    url: HttpUrl | None = None


class VersionControlInfo(BaseModel):
    provider: str
    repository: RepositoryInfo
    branch: BranchInfo
    commit: CommitInfo


class MostRecentMetadata(BaseModel):
    id: UUID
    total_files: int
    driver_ignored_files: int | None = None
    status: str
    total_sloc: int | None = None
    analyzable_sloc: int | None = None
    top_language: str | None = None
    analyzable_sloc_by_type: dict[str, int] | None = None


class MostRecentVersionContent(BaseModel):
    kind: list[str] | None = None
    domain: list[str] | None = None
    audience: list[str] | None = None
    content: str | None = None


class CodebaseCard(BaseModel):
    id: UUID
    organization_id: str
    kind: str
    source_type: str
    version_control: VersionControlInfo
    display_name: str
    primary_asset_created_at: datetime = Field(alias="created_at")
    primary_asset_updated_at: datetime = Field(alias="updated_at")
    codebase_settings_auto_commit_docs: bool | None = None
    status: str
    browsable: bool
    tags: list[TagRead]
    most_recent_metadata: MostRecentMetadata
    most_recent_version_content: MostRecentVersionContent | None = None

    model_config = {"populate_by_name": True}


# --------------------------------------------------------------------------------------
# Small helpers (unchanged)
# --------------------------------------------------------------------------------------


def _provider_to_source_type(provider: PrimaryAssetProvider) -> str:  # unchanged
    return {
        PrimaryAssetProvider.GITHUB: "Github Codebase",
        PrimaryAssetProvider.GITLAB_SELF_MANAGED: "Gitlab Codebase",
        PrimaryAssetProvider.BITBUCKET: "Bitbucket Codebase",
        PrimaryAssetProvider.USER: "ZIP Upload",
    }.get(provider, "Unknown")


def _safe_commit_sha(version: Version) -> str | None:  # unchanged
    disp = getattr(version, "display_name", None)
    cand = version.vcs_hash or disp
    if cand and str(cand).lower() == "unversioned":
        return None
    return str(cand) if cand else None


def _parse_asset_kinds(values: list[str] | None) -> list[PrimaryAssetKind]:  # unchanged
    if not values:
        return []
    kinds: list[PrimaryAssetKind] = []
    for raw in values:
        try:
            kinds.append(PrimaryAssetKind[raw.upper()])
        except KeyError:
            try:
                kinds.append(PrimaryAssetKind(raw.lower()))
            except ValueError:
                continue
    return kinds


def _extract_ordered_keys(md: dict[str, Any] | None) -> list[str] | None:  # unchanged
    if not md:
        return None
    return [k for k, _ in sorted(md.items(), key=lambda kv: (-float(kv[1]), kv[0]))][:3]


# --------------------------------------------------------------------------------------
# Main endpoint - optimised
# --------------------------------------------------------------------------------------

router = APIRouter()


@router.get("/", response_model=ListWithCount[CodebaseCard])
def codebase_card(
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    id: list[UUID] | None = Query(default=None),
    primary_asset_kind: list[str] | None = Query(default=None, alias="asset_kind"),
    codebase_kind: str | None = Query(default=None),
    codebase_domain: str | None = Query(default=None),
    codebase_audience: str | None = Query(default=None),
    top_language: str | None = Query(default=None),
) -> ListWithCount[CodebaseCard]:
    """
    Return a list of `CodebaseCard` objects.

    Identical output to the original implementation, but with **far fewer
    database round-trips** thanks to batched loading of `DerivedContent`.
    """

    # ------------------------------------------------------------------
    # 1. Build the sub-query that finds an organisation's PrimaryAssets
    # ------------------------------------------------------------------
    pa = aliased(PrimaryAsset)
    root = aliased(Node)

    completed_ver_id_subq = (
        select(Version.id)
        .where(
            Version.primary_asset_id == pa.id,
            Version.status == VersionStatus.GENERATION_COMPLETE,
        )
        .order_by(Version.updated_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    base_subq = (
        select(pa.id)
        .where(pa.organization_id == user.organization_id)
        .join(root, (root.version_id == completed_ver_id_subq) & (root.depth == 0))
    )

    # ------------------------------------------------------------------
    # 2. Apply user filters (same logic as original)
    # ------------------------------------------------------------------
    kinds = _parse_asset_kinds(primary_asset_kind) or [
        PrimaryAssetKind.CODEBASE,
        PrimaryAssetKind.FILE,
    ]
    base_subq = base_subq.where(pa.kind.in_(kinds))

    if id:
        base_subq = base_subq.where(pa.id.in_(id))

    if top_language:
        tl = [t.lower() for t in top_language]
        base_subq = base_subq.where(
            func.lower(root.misc_metadata["top_language_by_file_count"].astext).in_(tl)
            | func.lower(root.misc_metadata["top_language"].astext).in_(tl)
        )

    # derived-content filters
    def _add_dc_filter(
        q: select, key: str | None, dc_kind: ContentKind, alias_name: str
    ) -> select:
        if not key:
            return q
        dc_alias = aliased(DerivedContent, name=alias_name)
        cond = or_(dc_alias.misc_metadata.has_key(key))
        return q.join(
            dc_alias,
            (dc_alias.node_id == root.id) & (dc_alias.content_kind == dc_kind),
        ).where(cond)

    base_subq = _add_dc_filter(
        base_subq, codebase_kind, ContentKind.CODEBASE_KINDS, "dc_kinds"
    )
    base_subq = _add_dc_filter(
        base_subq, codebase_domain, ContentKind.CODEBASE_DOMAINS, "dc_domains"
    )
    base_subq = _add_dc_filter(
        base_subq, codebase_audience, ContentKind.CODEBASE_AUDIENCES, "dc_auds"
    )

    # Should pagination be applied at SQL level?
    apply_pagination = not (codebase_kind or codebase_domain or codebase_audience)

    # ------------------------------------------------------------------
    # 3. Main query: PrimaryAsset + its most recent completed Version
    # ------------------------------------------------------------------
    assets_stmt = (
        select(PrimaryAsset, Version)
        .join(Version, Version.primary_asset_id == PrimaryAsset.id)
        .where(
            PrimaryAsset.id.in_(base_subq.subquery()),
            Version.status == VersionStatus.GENERATION_COMPLETE,
        )
        .distinct(PrimaryAsset.id)
        .options(
            selectinload(PrimaryAsset.tags),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.root_node
            ),
        )
        .order_by(PrimaryAsset.id, Version.updated_at.desc())
    )
    total_count = session.exec(select(func.count()).select_from(assets_stmt)).one()
    if apply_pagination:
        assets_stmt = assets_stmt.offset(pagination.offset).limit(pagination.limit)

    # One round-trip to get all assets + their most-recent completed version
    assets_with_versions: list[tuple[PrimaryAsset, Version]] = (
        session.exec(assets_stmt).unique().all()
    )

    # ------------------------------------------------------------------
    # 4. Batch-load latest DerivedContent for *all* root nodes in one go
    # ------------------------------------------------------------------
    root_ids: list[UUID] = [
        v.root_node.id  # type: ignore[arg-type]
        for _, v in assets_with_versions
        if v and v.root_node
    ]
    if not root_ids:
        return []

    wanted_kinds = (
        ContentKind.CODEBASE_KINDS,
        ContentKind.CODEBASE_DOMAINS,
        ContentKind.CODEBASE_AUDIENCES,
        getattr(
            ContentKind,
            "TOP_LEVEL_TERSE_SENTENCE",
            ContentKind.TOP_LEVEL_TERSE_SENTENCE,
        ),
    )

    # ── rank each row per (node_id, content_kind) and keep rn == 1 ──────────────
    dc_ranked = (
        select(
            DerivedContent.id.label("dc_id"),
            func.row_number()
            .over(
                partition_by=(DerivedContent.node_id, DerivedContent.content_kind),
                order_by=DerivedContent.updated_at.desc(),
            )
            .label("rn"),
        )
        .where(
            DerivedContent.node_id.in_(root_ids),
            DerivedContent.content_kind.in_(wanted_kinds),
        )
        .cte("dc_ranked")
    )

    # bring back full ORM rows so we can use attribute access safely
    latest_dc_stmt = (
        select(DerivedContent)
        .join(dc_ranked, DerivedContent.id == dc_ranked.c.dc_id)
        .where(dc_ranked.c.rn == 1)
    )

    # one round-trip, returns real DerivedContent objects
    latest_dc_rows: list[DerivedContent] = session.exec(latest_dc_stmt).all()

    latest_dc: dict[tuple[UUID, ContentKind], DerivedContent] = {
        (row.node_id, row.content_kind): row for row in latest_dc_rows
    }

    cards: list[CodebaseCard] = []

    # If pagination was pushed to Python (because derived-content filters prevent SQL-side pagination)
    def _should_skip(idx: int) -> bool:
        return (not apply_pagination) and (
            idx < pagination.offset or len(cards) >= pagination.limit
        )

    for index, (pa_row, v_done) in enumerate(assets_with_versions):
        v_cur = pa_row.most_recent_version
        if v_cur is None:
            continue

        root_node: Node | None = v_done.root_node if v_done else None  # type: ignore
        if root_node is None:
            continue

        # Grab the latest derived-content rows from the lookup table
        def _dc(kind: ContentKind) -> DerivedContent | None:
            return latest_dc.get((root_node.id, kind))  # noqa: B023

        dc_kinds = _dc(ContentKind.CODEBASE_KINDS)
        dc_domains = _dc(ContentKind.CODEBASE_DOMAINS)
        dc_auds = _dc(ContentKind.CODEBASE_AUDIENCES)
        dc_terse = _dc(
            getattr(
                ContentKind,
                "TOP_LEVEL_TERSE_SENTENCE",
                ContentKind.TOP_LEVEL_TERSE_SENTENCE,
            )
        )

        kind_list = _extract_ordered_keys(dc_kinds.misc_metadata) if dc_kinds else None
        if codebase_kind and kind_list and kind_list[0] != codebase_kind:
            total_count -= 1
            continue

        domain_list = (
            _extract_ordered_keys(dc_domains.misc_metadata) if dc_domains else None
        )
        if codebase_domain and domain_list and domain_list[0] != codebase_domain:
            total_count -= 1
            continue

        audience_list = (
            _extract_ordered_keys(dc_auds.misc_metadata) if dc_auds else None
        )
        if (
            codebase_audience
            and audience_list
            and audience_list[0] != codebase_audience
        ):
            total_count -= 1
            continue
        if _should_skip(index):
            continue
        terse_sentence = dc_terse.content if dc_terse else None

        node_meta: dict[str, Any] = root_node.misc_metadata or {}
        sha = _safe_commit_sha(v_cur)
        vcs_meta = v_cur.vcs_metadata or {}
        repo_meta, branch_meta, commit_meta = (
            vcs_meta.get("repository", {}),
            vcs_meta.get("branch", {}),
            vcs_meta.get("commit", {}),
        )
        commit_block = CommitInfo(
            sha=sha,
            short_sha=sha[:8] if sha else None,
            message=commit_meta.get("message"),
            url=commit_meta.get("url"),
            author=CommitAuthor(
                name=commit_meta.get("author", {}).get("name"),
                email=commit_meta.get("author", {}).get("email"),
                date=commit_meta.get("author", {}).get("date") or v_cur.updated_at,
            ),
        )
        vc_block = VersionControlInfo(
            provider=pa_row.provider.value.lower(),
            repository=RepositoryInfo(
                name=repo_meta.get("name") or pa_row.display_name,
                namespace=repo_meta.get("namespace"),
                full_name=repo_meta.get("full_name")
                or repo_meta.get("name")
                or pa_row.display_name,
                url=repo_meta.get("url"),
            ),
            branch=BranchInfo(
                name=branch_meta.get("name") or "main",
                protected=branch_meta.get("protected", False),
            ),
            commit=commit_block,
        )
        meta_block = MostRecentMetadata(
            id=v_cur.id,
            total_files=(root_node.total_files or 1),
            driver_ignored_files=node_meta.get("driver_ignored_files"),
            status=v_cur.status.value,
            total_sloc=node_meta.get("total_sloc"),
            analyzable_sloc=node_meta.get("analyzable_sloc"),
            top_language=node_meta.get("top_language_by_file_count")
            or node_meta.get("top_language"),
            analyzable_sloc_by_type=node_meta.get("analyzable_sloc_by_type"),
        )

        mrv_content = MostRecentVersionContent(
            kind=kind_list,
            domain=domain_list,
            audience=audience_list,
            content=terse_sentence,
        )

        cards.append(
            CodebaseCard(
                id=pa_row.id,
                organization_id=pa_row.organization_id,
                kind=pa_row.kind.value,
                source_type=_provider_to_source_type(pa_row.provider),
                version_control=vc_block,
                display_name=pa_row.display_name,
                created_at=pa_row.created_at,
                updated_at=pa_row.updated_at,
                status=v_cur.status.value,
                codebase_settings_auto_commit_docs=pa_row.codebase_settings_auto_commit_docs,
                browsable=v_cur.browsable,
                tags=[TagRead.model_validate(t) for t in pa_row.tags],
                most_recent_metadata=meta_block,
                most_recent_version_content=mrv_content,
            )
        )

    return ListWithCount(
        results=cards,
        total_count=total_count,
    )
