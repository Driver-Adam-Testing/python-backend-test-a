from uuid import UUID

import modal
from database.models_v1 import DocumentSource
from database.models_v2 import AutoDocStatusHistory, Node, PrimaryAsset, Version
from database.models_v2_enums import AutoDocStatusMessageKind, VersionStatus
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

    node.version.status = VersionStatus.GENERATING
    session.add(node.version)

    run_autodoc = modal.Function.lookup(
        "autodocs",
        "run_adi_driver",
        environment_name=settings.MODAL_ENVIRONMENT,
    )

    call = run_autodoc.spawn(page_node_id=str(input.page_id))
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
        raise HTTPException(status_code=404, detail="No autodocs status found")

    return autodoc_status


@router.post("/cancel")
def cancel(
    user: UserToken,
    session: CurrentSession,
    input: AutoDocRequest,
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
