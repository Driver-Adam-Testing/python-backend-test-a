from uuid import UUID

import modal
from database.models_v1 import DocumentSource
from database.models_v2 import AutoDocStatusHistory, Node, PrimaryAsset, Version
from database.models_v2_enums import (
    AutoDocConfigKind,
    AutoDocStatusMessageKind,
    PrimaryAssetKind,
    VersionStatus,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import (
    UserToken,
)
from app.api.session import CurrentSession
from app.core.config import settings

router = APIRouter()


class AutoDocRequest(BaseModel):
    page_id: UUID
    config_kind: AutoDocConfigKind


class AutoDocCancelRequest(BaseModel):
    page_id: UUID


class AutoDocResponse(BaseModel):
    status: AutoDocStatusHistory


class AutoDocCancelResponse(BaseModel):
    status: str


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

        case AutoDocConfigKind.ARCHITECTURE:
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
                    detail="Architecture Overview requires at least one codebase source tuned",
                )
        case AutoDocConfigKind.CUSTOM:
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
                    detail="Custom Overview requires at least one codebase source tuned",
                )

        case _:
            raise HTTPException(
                status_code=400,
                detail="Invalid config",
            )
    run_autodoc = modal.Function.lookup(
        "autodocs",
        "run_autodoc",
        environment_name=settings.MODAL_ENVIRONMENT,
    )

    node.version.status = VersionStatus.GENERATING
    session.add(node.version)

    call = run_autodoc.spawn(
        page_node_id=str(input.page_id),
        config_kind=input.config_kind,
    )
    autodoc_status = AutoDocStatusHistory(
        page_node_id=input.page_id,
        status_kind=AutoDocStatusMessageKind.RETRIEVING_SOURCES,
        content="Retrieving sources for the page...",
        call_id=call.object_id,
    )
    session.add(autodoc_status)
    session.commit()
    session.refresh(autodoc_status)

    return autodoc_status


@router.get("/current_status/{page_id}")
def get_autodoc_current_status(
    user: UserToken,
    session: CurrentSession,
    page_id: UUID,
) -> AutoDocStatusHistory:
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
    call_id = autodoc_status.call_id
    call = modal.FunctionCall.from_id(call_id)
    call.cancel()

    return AutoDocCancelResponse(status="Autodocs generation cancelled")
