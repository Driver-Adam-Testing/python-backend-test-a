from __future__ import annotations

from datetime import datetime  # noqa: TCH003
from typing import Any
from uuid import UUID  # noqa: TCH003

from database.models import (
    DerivedContent,
    Node,
    PrimaryAsset,
    PrimaryAssetTag,
    Version,
)
from database.models_enums import (
    ContentKind,
    PrimaryAssetKind,
    PrimaryAssetProvider,
    VcsAutoUpdatePolicy,
    VersionStatus,
)
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import select

from app.api.auth import UserToken  # noqa: TCH001
from app.api.routes.v2.query_utils import (
    Pagination,
    apply_filters_to_query,
    apply_sorting_to_query,
)
from app.api.routes.v2.schemas import ListWithCount, TagRead
from app.api.session import CurrentSession  # noqa: TCH001
from app.authorization.query_filters import primary_asset_grant_filter


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
    name: str | None
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
    root_node_id: UUID | None = None
    total_files: int
    driver_ignored_files: int | None = None
    status: str
    total_sloc: int | None = None
    analyzable_sloc: int | None = None
    top_language: str | None = None
    analyzable_sloc_by_type: dict[str, int] | None = None
    analyzable_files_by_type: dict[str, int] | None = None


class MostRecentVersionContent(BaseModel):
    root_node_id: UUID | None = None
    kind: list[str] | None = None
    domain: list[str] | None = None
    audience: list[str] | None = None
    content: str | None = None


class CodebaseCard(BaseModel):
    id: UUID
    vcs_auto_update_policy: VcsAutoUpdatePolicy | None
    organization_id: str
    kind: str
    source_type: str
    version_control: VersionControlInfo | None
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


def _provider_to_source_type(
    provider: PrimaryAssetProvider, kind: PrimaryAssetKind
) -> str:
    if provider == PrimaryAssetProvider.USER:
        return {
            PrimaryAssetKind.CODEBASE: "Zip Upload",
            PrimaryAssetKind.FILE: "PDF Upload",
        }.get(kind, "Unknown")
    else:
        return {
            PrimaryAssetProvider.GITHUB: "Github Codebase",
            PrimaryAssetProvider.GITLAB_SELF_MANAGED: "Gitlab Codebase",
            PrimaryAssetProvider.BITBUCKET: "Bitbucket Codebase",
            PrimaryAssetProvider.AZURE_DEVOPS_CLOUD: "Azure DevOps Codebase",
        }.get(provider, "Unknown")


def _safe_commit_sha(version: Version) -> str | None:
    disp = getattr(version, "display_name", None)
    cand = version.vcs_hash or disp
    if cand and str(cand).lower() == "unversioned":
        return None
    return str(cand) if cand else None


def _parse_asset_kinds(values: list[str] | None) -> list[PrimaryAssetKind]:
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


def _extract_ordered_keys(md: dict[str, Any] | None) -> list[str] | None:
    if not md:
        return None
    return [k for k, _ in sorted(md.items(), key=lambda kv: (-float(kv[1]), kv[0]))][:3]


router = APIRouter()


@router.get("/", response_model=ListWithCount[CodebaseCard])
def codebase_card(
    request: Request,
    session: CurrentSession,
    user: UserToken,
    pagination: Pagination,
    id: list[UUID] | None = Query(default=None),
    primary_asset_kind: list[str] | None = Query(default=None, alias="asset_kind"),
    codebase_kind: str | None = Query(default=None),
    codebase_domain: str | None = Query(default=None),
    codebase_audience: str | None = Query(default=None),
    top_language: str | None = Query(default=None),
    tag_ids: str | None = Query(default=None),
) -> ListWithCount[CodebaseCard]:
    """
    Return a list of `CodebaseCard` objects.

    Identical output to the original implementation, but with **far fewer
    database round-trips** thanks to batched loading of `DerivedContent`.

    This endpoint filters assets based on the user's grants to the PrimaryAsset.
    Users will only see assets they have access to via:
    - Super admin role (see all assets in org)
    - Direct user grants
    - Team membership grants
    - Organization-wide grants
    - Public grants
    """

    pa = aliased(PrimaryAsset)
    root = aliased(Node)

    completed_ver_id_subq = (
        select(Version.id)
        .where(
            Version.primary_asset_id == pa.id,
            Version.status == VersionStatus.GENERATION_COMPLETE,
        )
        .order_by(Version.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    base_subq = (
        select(pa.id)
        .where(pa.organization_id == user.organization_id)
        .where(primary_asset_grant_filter(session, user.user_id, user.organization_id))
        .outerjoin(root, (root.version_id == completed_ver_id_subq) & (root.depth == 0))
    )

    kinds = _parse_asset_kinds(primary_asset_kind) or [
        PrimaryAssetKind.CODEBASE,
        PrimaryAssetKind.FILE,
    ]
    base_subq = base_subq.where(pa.kind.in_(kinds))

    if id:
        base_subq = base_subq.where(pa.id.in_(id))

    if top_language:
        tl = [t.lower() for t in top_language.split(",")]
        base_subq = base_subq.where(
            func.lower(root.misc_metadata["top_language_by_file_count"].astext).in_(tl)
            | func.lower(root.misc_metadata["top_language"].astext).in_(tl)
        )

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

    apply_pagination = not (codebase_kind or codebase_domain or codebase_audience)
    latest_complete_versions_subq = (
        select(
            Version.id.label("v_id"),
            Version.primary_asset_id,
            func.row_number()
            .over(
                partition_by=Version.primary_asset_id,
                order_by=Version.created_at.desc(),
            )
            .label("rn"),
        )
        .where(Version.status == VersionStatus.GENERATION_COMPLETE)
        .cte("most_recent_version_complete_subq")
    )
    latest_versions_subq = select(
        Version.id.label("v_id"),
        Version.primary_asset_id,
        func.row_number()
        .over(
            partition_by=Version.primary_asset_id,
            order_by=Version.created_at.desc(),
        )
        .label("rn"),
    ).cte("most_recent_version_subq")

    latest_complete_version = aliased(Version)
    latest_version = aliased(Version)
    latest_version_root_node = aliased(Node)
    latest_complete_version_root_node = aliased(Node)
    assets_stmt = (
        select(
            PrimaryAsset,
            latest_version,
            latest_complete_version,
            latest_version_root_node,
            latest_complete_version_root_node,
        )
        .outerjoin(
            latest_complete_versions_subq,
            PrimaryAsset.id == latest_complete_versions_subq.c.primary_asset_id,
        )
        .outerjoin(
            latest_complete_version,
            latest_complete_version.id == latest_complete_versions_subq.c.v_id,
        )
        .join(
            latest_versions_subq,
            and_(
                PrimaryAsset.id == latest_versions_subq.c.primary_asset_id,
                latest_versions_subq.c.rn == 1,
            ),
        )
        .join(
            latest_version,
            latest_version.id == latest_versions_subq.c.v_id,
        )
        .outerjoin(
            latest_version_root_node,
            and_(
                latest_version_root_node.version_id == latest_version.id,
                latest_version_root_node.depth == 0,
            ),
        )
        .outerjoin(
            latest_complete_version_root_node,
            and_(
                latest_complete_version_root_node.version_id
                == latest_complete_version.id,
                latest_complete_version_root_node.depth == 0,
            ),
        )
        .where(
            or_(
                latest_complete_versions_subq.c.rn == 1,
                latest_complete_versions_subq.c.rn.is_(None),
            ),
            PrimaryAsset.id.in_(base_subq.subquery()),
        )
        .options(
            selectinload(PrimaryAsset.tags),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.root_node
            ),
            selectinload(PrimaryAsset.most_recent_version).selectinload(
                Version.creator
            ),
        )
    )
    assets_stmt = apply_filters_to_query(
        assets_stmt, request.query_params, PrimaryAsset
    )
    if tag_ids:
        assets_stmt = assets_stmt.where(
            select(PrimaryAssetTag)
            .where(PrimaryAssetTag.primary_asset_id == PrimaryAsset.id)
            .where(PrimaryAssetTag.tag_id.in_(tag_ids.split(",")))
            .exists()
        )
    total_count = session.exec(select(func.count()).select_from(assets_stmt)).one()
    assets_stmt = apply_sorting_to_query(assets_stmt, pagination, PrimaryAsset)
    if apply_pagination:
        assets_stmt = assets_stmt.offset(pagination.offset).limit(pagination.limit)

    assets_with_versions: list[tuple[PrimaryAsset, Version, Version, Node, Node]] = (
        session.exec(assets_stmt).unique().all()
    )

    complete_root_ids: list[UUID] = [
        latest_complete_version_root_node.id
        for _, _, _, latest_version_root_node, _ in assets_with_versions
        if latest_version_root_node
    ]
    recent_root_ids: list[UUID] = [
        latest_version_root_node.id
        for _, _, _, latest_version_root_node, _ in assets_with_versions
        if latest_version_root_node
    ]
    if not recent_root_ids:
        # Only codebases in Connecting?
        connecting_cards = []
        for pa_row, v_latest, _, _, _ in assets_with_versions:
            sha = _safe_commit_sha(v_latest)
            if (
                pa_row.kind == PrimaryAssetKind.CODEBASE
                and pa_row.provider != PrimaryAssetProvider.USER
            ):
                vcs_meta = v_latest.vcs_metadata or {}
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
                        date=commit_meta.get("author", {}).get("date")
                        or pa_row.most_recent_version.updated_at,
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
                        name=branch_meta.get("name"),
                        protected=branch_meta.get("protected", False),
                    ),
                    commit=commit_block,
                )
            else:
                vc_block = None
            meta_block = MostRecentMetadata(
                id=v_latest.id,
                root_node_id=None,  # No root id in Connecting
                total_files=0,
                driver_ignored_files=0,
                status=v_latest.status.value,
                total_sloc=0,
                analyzable_sloc=0,
                top_language=None,
                analyzable_sloc_by_type=None,
                analyzable_files_by_type=None,
            )

            mrv_content = MostRecentVersionContent(
                root_node_id=None,  # No root id in Connecting
                kind=None,
                domain=None,
                audience=None,
                content=None,
            )
            connecting_cards.append(
                CodebaseCard(
                    id=pa_row.id,
                    vcs_auto_update_policy=pa_row.vcs_auto_update_policy,
                    organization_id=pa_row.organization_id,
                    kind=pa_row.kind.value,
                    source_type=_provider_to_source_type(pa_row.provider, pa_row.kind),
                    version_control=vc_block,
                    display_name=pa_row.display_name,
                    created_at=pa_row.created_at,
                    updated_at=pa_row.updated_at,
                    status=v_latest.status.value,
                    codebase_settings_auto_commit_docs=pa_row.codebase_settings_auto_commit_docs,
                    browsable=v_latest.browsable,
                    tags=[TagRead.model_validate(t) for t in pa_row.tags],
                    most_recent_metadata=meta_block,
                    most_recent_version_content=mrv_content,
                )
            )
        return ListWithCount(
            results=connecting_cards, total_count=len(connecting_cards)
        )

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
            DerivedContent.node_id.in_(complete_root_ids),
            DerivedContent.content_kind.in_(wanted_kinds),
        )
        .cte("dc_ranked")
    )

    latest_dc_stmt = (
        select(DerivedContent)
        .join(dc_ranked, DerivedContent.id == dc_ranked.c.dc_id)
        .where(dc_ranked.c.rn == 1)
    )

    latest_dc_rows: list[DerivedContent] = session.exec(latest_dc_stmt).all()

    latest_dc: dict[tuple[UUID, ContentKind], DerivedContent] = {
        (row.node_id, row.content_kind): row for row in latest_dc_rows
    }

    cards: list[CodebaseCard] = []

    def _should_skip(idx: int) -> bool:
        return (not apply_pagination) and (
            idx < pagination.offset or len(cards) >= pagination.limit
        )

    for index, (
        pa_row,
        v_latest,
        _,
        latest_version_root_node,
        latest_complete_version_root_node,
    ) in enumerate(assets_with_versions):  # type: ignore[arg-type]
        if v_latest is None:
            continue

        root_node_complete: Node | None = latest_complete_version_root_node
        root_node_latest: Node | None = latest_version_root_node

        def _dc(kind: ContentKind) -> DerivedContent | None:
            if root_node_complete is None:  # noqa: B023
                return {}
            return latest_dc.get((root_node_complete.id, kind))  # noqa: B023

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

        node_meta: dict[str, Any] | None = (
            root_node_latest.misc_metadata if root_node_latest else None
        )
        node_meta = node_meta or {}

        sha = _safe_commit_sha(v_latest)
        if (
            pa_row.kind == PrimaryAssetKind.CODEBASE
            and pa_row.provider != PrimaryAssetProvider.USER
        ):
            vcs_meta = v_latest.vcs_metadata or {}
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
                    date=commit_meta.get("author", {}).get("date")
                    or pa_row.most_recent_version.updated_at,
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
                    name=branch_meta.get("name"),
                    protected=branch_meta.get("protected", False),
                ),
                commit=commit_block,
            )
        else:
            vc_block = None

        meta_block = MostRecentMetadata(
            id=v_latest.id,
            root_node_id=root_node_latest.id if root_node_latest else None,
            total_files=(
                root_node_latest.total_files
                if root_node_latest and root_node_latest.total_files
                else 1
            ),
            driver_ignored_files=node_meta.get("driver_ignored_files"),
            status=v_latest.status.value,
            total_sloc=node_meta.get("total_sloc"),
            analyzable_sloc=node_meta.get("analyzable_sloc"),
            top_language=node_meta.get("top_language_by_file_count")
            or node_meta.get("top_language"),
            analyzable_sloc_by_type=node_meta.get("analyzable_sloc_by_type"),
            analyzable_files_by_type=node_meta.get("analyzable_files_by_type"),
        )

        mrv_content = MostRecentVersionContent(
            root_node_id=root_node_complete.id if root_node_complete else None,
            kind=kind_list,
            domain=domain_list,
            audience=audience_list,
            content=terse_sentence,
        )

        cards.append(
            CodebaseCard(
                id=pa_row.id,
                vcs_auto_update_policy=pa_row.vcs_auto_update_policy,
                organization_id=pa_row.organization_id,
                kind=pa_row.kind.value,
                source_type=_provider_to_source_type(pa_row.provider, pa_row.kind),
                version_control=vc_block,
                display_name=pa_row.display_name,
                created_at=pa_row.created_at,
                updated_at=pa_row.updated_at,
                status=v_latest.status.value,
                codebase_settings_auto_commit_docs=pa_row.codebase_settings_auto_commit_docs,
                browsable=v_latest.browsable,
                tags=[TagRead.model_validate(t) for t in pa_row.tags],
                most_recent_metadata=meta_block,
                most_recent_version_content=mrv_content,
            )
        )

    return ListWithCount(
        results=cards,
        total_count=total_count or 0,
    )
