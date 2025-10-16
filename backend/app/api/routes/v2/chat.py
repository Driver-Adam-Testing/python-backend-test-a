from uuid import UUID

from database.models import Node
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3.app.pipelines.chat import (
    ChatPipelineRequest,
)  # local import after FastAPI deps
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action

router = APIRouter()


class ChatHttpRequest(BaseModel):
    user_prompt: str
    source_node_ids: list[UUID] | None = None
    page_node_id: UUID | None = None
    llm_session_id: UUID | None = None
    relative_paths: list[str] | None = None


@router.post("/", response_class=StreamingResponse)
async def create_streaming_post(
    session: CurrentSession,
    user: UserToken,
    payload: ChatHttpRequest,
) -> StreamingResponse:
    query = (
        select(Node)
        .where(Node.id.in_(payload.source_node_ids))
        .options(selectinload(Node.version))
    )
    nodes = session.exec(query).all()
    for node in nodes:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=node.version.primary_asset_id,
            action_key="asset.use_as_source",
        )
    request = ChatPipelineRequest(
        user_prompt=payload.user_prompt,
        node_ids=payload.source_node_ids,
        page_node_id=payload.page_node_id,
        organization_id=user.organization_id,
        user_id=user.user_id,
        relative_paths=payload.relative_paths,
        llm_session_id=payload.llm_session_id,
    )

    return StreamingResponse(request.stream(), media_type="text/event-stream")
