"""
app/api/routes/v2/codebase_cards.py
-----------------------------------

Return “CodebaseCards” for every PrimaryAsset that:

* belongs to the caller's organisation;
* optionally matches an explicit PrimaryAsset ID list;
* matches one or more PrimaryAsset.kind values (CODEBASE, FILE, …);
* matches **top-language** directly in SQL (Node.misc_metadata);
* matches requested CODEBASE_KINDS / _DOMAINS / _AUDIENCES
  (keys inside JSONB on the derived-content rows that hang off the
  root node of the most-recent COMPLETED version).

The query pulls:

* **pa** - the PrimaryAsset row
* **v_cur** - pa.most_recent_version (current status)
* **v_done** - most-recent COMPLETED Version
* **root_done** - root node of v_done
* three DerivedContent rows hanging off root_done
  (for kinds, domains, audiences) - used only for SQL filtering
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

from app.api.routes.v2.schemas import TagRead

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from app.api.auth import UserToken
    from app.api.session import CurrentSession

router = APIRouter()

# --------------------------------------------------------------------------- #
# Response schemas (simple - use built-ins `list`/`dict`)                     #
# --------------------------------------------------------------------------- #


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
    browsable: bool
    tags: list[TagRead]
    most_recent_metadata: MostRecentMetadata
    most_recent_version_content: MostRecentVersionContent | None = None

    model_config = {"populate_by_name": True}


def _provider_to_source_type(provider: PrimaryAssetProvider) -> str:
    mapping = {
        PrimaryAssetProvider.GITHUB: "Github Codebase",
        PrimaryAssetProvider.GITLAB_SELF_MANAGED: "Gitlab Codebase",
        PrimaryAssetProvider.BITBUCKET: "Bitbucket Codebase",
        PrimaryAssetProvider.USER: "ZIP Upload",
    }
    return mapping.get(provider, "Unknown")


def _safe_commit_sha(version: Version) -> str | None:
    display_name = getattr(version, "display_name", None)
    candidate = version.vcs_hash or display_name
    if candidate and str(candidate).lower() == "unversioned":
        return None
    return str(candidate) if candidate else None


def _parse_asset_kinds(values: list[str] | None) -> list[PrimaryAssetKind]:
    kinds: list[PrimaryAssetKind] = []
    if not values:
        return kinds
    for raw in values:
        try:
            kinds.append(PrimaryAssetKind[raw.upper()])
            continue
        except KeyError:
            pass
        try:
            kinds.append(PrimaryAssetKind(raw.lower()))
        except ValueError:
            continue
    return kinds


# --------------------------------------------------------------------------- #
# Endpoint                                                                    #
# --------------------------------------------------------------------------- #


@router.get("/", response_model=list[CodebaseCard])
def codebase_card(
    session: CurrentSession,
    user: UserToken,
    # ---- PrimaryAsset-level filters -------------------------------- #
    id: list[UUID] | None = Query(
        default=None, description="One or more PrimaryAsset IDs to include"
    ),
    primary_asset_kind: list[str] | None = Query(
        default=None, alias="asset_kind", description="CODEBASE, FILE, ..."
    ),
    # ---- Codebase metadata filters (derived-content) --------------- #
    codebase_kinds: list[str] | None = Query(default=None),
    codebase_domains: list[str] | None = Query(default=None),
    codebase_audiences: list[str] | None = Query(default=None),
    # ---- Language filter (root-node JSON) -------------------------- #
    top_language: list[str] | None = Query(default=None),
) -> list[CodebaseCard]:
    """
    One DB round-trip:

    * sub-query gets IDs of assets that satisfy **all** requested filters;
    * main query fetches those assets with relationships eager-loaded
      so we can build the response in Python with zero additional queries.
    """

    # ------------------------ build filter sub-query ---------------- #

    pa = aliased(PrimaryAsset)

    # Most-recent COMPLETED Version per asset
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

    # Root node of that completed version
    root = aliased(Node)
    base_subq = (
        select(pa.id)
        .where(pa.organization_id == user.organization_id)
        .join(
            root,
            (root.version_id == completed_ver_id_subq) & (root.depth == 0),
        )
    )

    # ---------------- primary-asset filters ------------------------ #
    kinds = _parse_asset_kinds(primary_asset_kind) or [
        PrimaryAssetKind.CODEBASE,
        PrimaryAssetKind.FILE,
    ]
    base_subq = base_subq.where(pa.kind.in_(kinds))

    if id:
        base_subq = base_subq.where(pa.id.in_(id))

    # ---------------- top-language filter -------------------------- #
    if top_language:
        tlower = [t.lower() for t in top_language]
        base_subq = base_subq.where(
            func.lower(root.misc_metadata["top_language_by_file_count"].astext).in_(
                tlower
            )
            | func.lower(root.misc_metadata["top_language"].astext).in_(tlower)
        )

    # ------------------- derived-content filters ------------------- #
    def _add_dc_filter(
        query: select,
        keys: list[str] | None,
        dc_kind: ContentKind,
        alias_name: str,
    ) -> select:
        if not keys:
            return query
        dc_alias = aliased(DerivedContent, name=alias_name)
        conditions = or_(*[dc_alias.misc_metadata.has_key(k) for k in keys])
        return query.join(
            dc_alias,
            (dc_alias.node_id == root.id) & (dc_alias.content_kind == dc_kind),
        ).where(conditions)

    base_subq = _add_dc_filter(
        base_subq, codebase_kinds, ContentKind.CODEBASE_KINDS, "dc_kinds"
    )
    base_subq = _add_dc_filter(
        base_subq, codebase_domains, ContentKind.CODEBASE_DOMAINS, "dc_domains"
    )
    base_subq = _add_dc_filter(
        base_subq, codebase_audiences, ContentKind.CODEBASE_AUDIENCES, "dc_audiences"
    )

    filter_subq = base_subq.subquery()

    # ------------------------- main query -------------------------- #
    stmt = (
        select(PrimaryAsset)
        .where(PrimaryAsset.id.in_(select(filter_subq.c.id)))
        .options(
            selectinload(PrimaryAsset.tags),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.root_node
            ),
        )
        .order_by(PrimaryAsset.updated_at.desc())
    )

    assets: list[PrimaryAsset] = (
        session.exec(stmt).unique().all()  # type: ignore[arg-type]
    )

    # ---------------------------------------------------------------- #
    # Build response                                                   #
    # ---------------------------------------------------------------- #
    cards: list[CodebaseCard] = []
    for pa_row in assets:
        v_cur = pa_row.most_recent_version
        if v_cur is None:
            continue  # data inconsistency

        # -------- find most-recent COMPLETED version (may be same) --- #
        v_done: Version | None = session.exec(
            select(Version)
            .where(
                Version.primary_asset_id == pa_row.id,
                Version.status == VersionStatus.GENERATION_COMPLETE,
            )
            .order_by(Version.updated_at.desc())
            .limit(1)
        ).one_or_none()

        root_done: Node | None = (
            v_done.root_node if v_done else None  # type: ignore[attr-defined]
        )
        node_meta: dict[str, Any] = root_done.misc_metadata if root_done else {}
        if node_meta is None:
            node_meta = {}
        vcs_meta: dict[str, Any] = v_cur.vcs_metadata or {}
        repo_meta = vcs_meta.get("repository", {})
        branch_meta = vcs_meta.get("branch", {})
        commit_meta = vcs_meta.get("commit", {})

        sha = _safe_commit_sha(v_cur)
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

        # ---------------- metadata block ----------------------------- #
        meta_block = MostRecentMetadata(
            id=v_cur.id,
            total_files=(root_done.total_files if root_done else None) or 1,
            driver_ignored_files=node_meta.get("driver_ignored_files", None),
            status=v_cur.status.value,
            total_sloc=node_meta.get("total_sloc", 0),
            analyzable_sloc=node_meta.get("analyzable_sloc", 0),
            top_language=node_meta.get("top_language_by_file_count", None)
            or node_meta.get("top_language", None),
            analyzable_sloc_by_type=node_meta.get("analyzable_sloc_by_type", None),
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
                codebase_settings_auto_commit_docs=pa_row.codebase_settings_auto_commit_docs,
                browsable=v_cur.browsable,
                tags=[TagRead.model_validate(t) for t in pa_row.tags],
                most_recent_metadata=meta_block,
                most_recent_version_content=None,  # future work
            )
        )

    return cards
