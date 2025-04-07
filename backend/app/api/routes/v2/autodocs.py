from uuid import UUID

import modal
from database.models_v2 import Node, PrimaryAsset, Version, WhizStatusHistory
from database.models_v2_enums import VersionStatus, WhizStatus
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


class WhizRequest(BaseModel):
    page_id: UUID


class WhizResponse(BaseModel):
    status: WhizStatusHistory


@router.post(
    "/generate",
    summary="Generate whizdoodler page",
)
def run_whizdoodler(
    user: UserToken,
    session: CurrentSession,
    input: WhizRequest,
) -> WhizStatusHistory:
    node = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == user.organization_id)
        .where(Node.id == input.page_id)
        .options(selectinload(Node.version))
    ).one()
    # TODO: check for sources - return error code if none

    node.version.status = VersionStatus.GENERATING
    session.add(node.version)

    whiz_status = WhizStatusHistory(
        page_node_id=input.page_id,
        status=WhizStatus.RETRIEVING_SOURCES,
        content="Retrieving sources for the page...",
    )
    session.add(whiz_status)
    session.commit()
    session.refresh(whiz_status)

    run_whiz = modal.Function.lookup(
        "whizdoodler", "run_adi_driver", environment_name=settings.MODAL_ENVIRONMENT
    )

    run_whiz.spawn(page_node_id=str(input.page_id))

    return whiz_status


# TODO: endpoint to query the status


@router.get("/current_status")
def get_current_status(
    user: UserToken,
    session: CurrentSession,
    input: WhizRequest,
) -> WhizStatusHistory:
    whiz_status = session.exec(
        select(WhizStatusHistory)
        .where(WhizStatusHistory.page_node_id == input.page_id)
        .order_by(WhizStatusHistory.created_at.desc())
    ).first()

    if not whiz_status:
        raise HTTPException(status_code=404, detail="No autodocs status found")

    return whiz_status
