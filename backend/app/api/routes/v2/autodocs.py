from datetime import UTC, datetime
from enum import StrEnum
from logging import getLogger
from uuid import UUID

from database.models import (
    AutoDocStatusHistory,
    DocumentSource,
    Node,
    PrimaryAsset,
    Version,
)
from database.models_enums import (
    AutoDocConfigKind,
    AutoDocStatusMessageKind,
    PrimaryAssetKind,
    VersionStatus,
)
from fastapi import APIRouter, HTTPException
from hatchet_sdk import Hatchet
from pydantic import BaseModel, model_validator
from shared.interfaces.hatchet_interfaces import AutodocInput
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import (
    UserToken,
)
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action
from app.services.onboarding_checklist_service import OnboardingChecklistService

router = APIRouter()

logger = getLogger(__name__)


class AutoDocSize(StrEnum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"
    UNBOUND = "UNBOUND"


class AutoDocRequest(BaseModel):
    page_id: UUID
    config_kind: AutoDocConfigKind
    document_goal: str | None = None
    autodoc_size: AutoDocSize | None = None

    @model_validator(mode="after")
    def validate(self) -> "AutoDocRequest":
        if self.config_kind == AutoDocConfigKind.FROM_DOCUMENT_GOAL:
            if not self.document_goal:
                raise ValueError(
                    "document_goal is required when config_kind is FROM_DOCUMENT_GOAL"
                )
            if not self.autodoc_size:
                raise ValueError(
                    "autodoc_size is required when config_kind is FROM_DOCUMENT_GOAL"
                )
        return self


class AutoDocCancelRequest(BaseModel):
    page_id: UUID


class AutoDocCancelResponse(BaseModel):
    status: str


def _autodoc_size_to_user_context(autodoc_size: AutoDocSize) -> str:
    USER_CONTEXT_BASE = "The final TOML configuration file shall include the minimum number of sections required to adequately fulfil the document goal."

    if autodoc_size == AutoDocSize.UNBOUND:
        return USER_CONTEXT_BASE

    match autodoc_size:
        case AutoDocSize.SHORT:
            section_range = (1, 3)
        case AutoDocSize.MEDIUM:
            section_range = (4, 6)
        case AutoDocSize.LONG:
            section_range = (7, 10)

    return f"{USER_CONTEXT_BASE}  It should include a minimum of {section_range[0]} sections and no more than {section_range[1]} sections."


@router.post(
    "/generate",
    summary="Generate autodoc page",
)
def run_autodoc(
    user: UserToken,
    session: CurrentSession,
    input: AutoDocRequest,
) -> AutoDocStatusHistory:
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(Node.id == input.page_id)
        .options(selectinload(Node.version))
    ).one()

    document_sources = session.exec(
        select(DocumentSource)
        .where(DocumentSource.page_node_id == input.page_id)
        .options(
            selectinload(DocumentSource.source_node)
            .selectinload(Node.version)
            .selectinload(Version.primary_asset)
        )
    ).all()

    for source in document_sources:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=source.source_node.version.primary_asset_id,
            action_key="asset.use_as_source",
        )

    if not document_sources:
        raise HTTPException(
            status_code=404,
            detail="No document sources found for the page",
        )

    if node.version.status == VersionStatus.GENERATING:
        raise HTTPException(
            status_code=400,
            detail="Autodoc is already generating for this page",
        )

    match input.config_kind:
        case AutoDocConfigKind.ADI_DRIVER:
            # TODO: this check is a temporary guardrail while ADI is using this just for drivers
            # TODO: We could do an org check here, but it gets messy with dev/staging/prod.
            # This is low risk to be hit by other organizations though, and there is no data leakage concern here since
            # no-os is an open source repo.
            code_node_count = 0
            for document_source in document_sources:
                if (
                    document_source.source_node.version.primary_asset.kind
                    == PrimaryAssetKind.CODEBASE
                ):
                    code_node_count += 1
                if (
                    (
                        document_source.source_node.version.primary_asset.kind
                        == PrimaryAssetKind.CODEBASE
                    )
                    and document_source.source_node.depth <= 1
                ) or (code_node_count >= 4):
                    raise HTTPException(
                        status_code=400,
                        detail="Tune sources to only include at most a single driver and single project subfolder",
                    )

        case (
            AutoDocConfigKind.ARCHITECTURE
            | AutoDocConfigKind.CUSTOM
            | AutoDocConfigKind.FROM_DOCUMENT_GOAL
        ):
            code_node_count = 0
            for document_source in document_sources:
                if (
                    document_source.source_node.version.primary_asset.kind
                    == PrimaryAssetKind.CODEBASE
                ):
                    code_node_count += 1
            if code_node_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Sources must include at least one codebase.",
                )

        case _:
            raise HTTPException(
                status_code=400,
                detail="Invalid config",
            )
    hatchet = Hatchet()
    autodocs_task = hatchet.stubs.task(
        name="autodocs-workflow",
        input_validator=AutodocInput,
    )

    node.version.status = VersionStatus.GENERATING
    session.add(node.version)

    call = autodocs_task.run_no_wait(
        AutodocInput(
            page_node_id=str(input.page_id),
            config_kind=input.config_kind,
            document_goal=input.document_goal,
            user_context=_autodoc_size_to_user_context(input.autodoc_size)
            if input.autodoc_size
            else None,
            content_kind=None,
        )
    )
    autodoc_status = AutoDocStatusHistory(
        page_node_id=input.page_id,
        status_kind=AutoDocStatusMessageKind.RETRIEVING_SOURCES,
        content="Retrieving sources for the page...",
        call_id=str(call.workflow_run_id),
    )
    session.add(autodoc_status)
    session.commit()
    session.refresh(autodoc_status)

    OnboardingChecklistService.get_or_create_checklist(
        session=session,
        organization_id=user.organization_id,
        user_id=user.user_id,
    ).mark_generate_autodoc_completed(datetime.now(UTC))

    return autodoc_status


@router.get("/current_status/{page_id}")
def get_autodoc_current_status(
    user: UserToken,
    session: CurrentSession,
    page_id: UUID,
) -> AutoDocStatusHistory:
    # TODO: enforce authorization check against the list of source assets
    # node = session.exec(
    #     select(Node)
    #     .join(Version)
    #     .join(PrimaryAsset)
    #     .where(PrimaryAsset.organization_id == user.organization_id)
    #     .where(Node.id == page_id)
    #     .options(selectinload(Node.version))
    # ).one()
    # enforce_asset_action(
    #     db=session,
    #     user=user,
    #     asset_id=node.version.primary_asset_id,
    #     action_key="autodocs.manage"
    # )
    autodoc_status = session.exec(
        select(AutoDocStatusHistory)
        .where(AutoDocStatusHistory.page_node_id == page_id)
        .order_by(AutoDocStatusHistory.created_at.desc())
    ).first()

    if not autodoc_status:
        return AutoDocStatusHistory(
            page_node_id=page_id,
            status_kind=AutoDocStatusMessageKind.NOT_STARTED,
            content="Autodoc generation has not started for this page",
        )

    return autodoc_status


@router.post("/cancel")
def cancel(
    user: UserToken,
    session: CurrentSession,
    input: AutoDocCancelRequest,
) -> AutoDocCancelResponse:
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(Node.id == input.page_id)
        .options(selectinload(Node.version))
    ).one()
    # TODO: enforce authorization check against the list of source assets
    # enforce_asset_action(
    #     db=session,
    #     user=user,
    #     asset_id=node.version.primary_asset_id,
    #     action_key="autodocs.manage"
    # )
    if node.version.status != VersionStatus.GENERATING:
        raise HTTPException(
            status_code=400,
            detail="Autodocs is not currently generating",
        )
    node.version.status = (
        VersionStatus.GENERATION_COMPLETE
    )  # This returns to the normal state of a page
    session.add(node.version)
    session.commit()

    autodoc_status = session.exec(
        select(AutoDocStatusHistory)
        .where(AutoDocStatusHistory.page_node_id == input.page_id)
        .order_by(AutoDocStatusHistory.created_at.desc())
    ).first()
    if not autodoc_status:
        raise HTTPException(status_code=404, detail="No autodocs status found")
    hatchet = Hatchet()
    hatchet.runs.cancel(autodoc_status.call_id)

    return AutoDocCancelResponse(status="Autodocs generation cancelled")
