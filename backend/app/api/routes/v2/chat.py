from uuid import UUID

from database.models import DocumentSource, Node, VersionNode
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3.app.pipelines.chat import (
    ChatPipelineRequest,
)

# local import after FastAPI deps
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import UserToken
from app.api.session import CurrentSession
from app.authorization.fastapi import enforce_asset_action

router = APIRouter()


class ChatHttpRequest(BaseModel):
    user_prompt: str
    # FURNISSJ: rename these variables
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
    source_ids = payload.source_node_ids or []
    if payload.page_node_id:
        sources_query = select(DocumentSource).where(
            DocumentSource.page_version_node_id == payload.page_node_id
        )
        sources = session.exec(sources_query).all()
        for source in sources:
            if source.source_version_node_id not in source_ids:
                source_ids.append(source.source_version_node_id)

    query = (
        select(VersionNode)
        .where(VersionNode.id.in_(source_ids))
        .options(selectinload(VersionNode.version))
    )
    version_nodes = session.exec(query).all()
    for version_node in version_nodes:
        enforce_asset_action(
            db=session,
            user=user,
            asset_id=version_node.version.primary_asset_id,
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
