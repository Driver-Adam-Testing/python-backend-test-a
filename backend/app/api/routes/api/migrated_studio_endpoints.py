from app.api.auth import ApiKeyToken
from app.api.routes.v2.chat import ChatHttpRequest
from app.api.routes.v2.contents import _list_contents
from app.api.routes.v2.primary_assets import _list_primary_assets
from app.api.routes.v2.query_utils import Pagination
from app.api.routes.v2.schemas import (
    ContentDetailRead,
    ListWithCount,
    PrimaryAssetDetailRead,
)
from app.api.session import CurrentSession
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from shared.v3.app.pipelines.chat import ChatPipelineRequest

router = APIRouter()


@router.post("/chat", response_class=StreamingResponse)
async def create_streaming_post(
    session: CurrentSession,
    user: ApiKeyToken,
    payload: ChatHttpRequest,
) -> StreamingResponse:
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


@router.get("/primary_assets", response_model=ListWithCount[PrimaryAssetDetailRead])
def get_primary_assets(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    pagination: Pagination,
    tag_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    return _list_primary_assets(request, session, user, pagination, tag_ids)


@router.get("/contents", response_model=ListWithCount[ContentDetailRead])
def get_contents(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    pagination: Pagination,
) -> ListWithCount[ContentDetailRead]:
    return _list_contents(request, session, user, pagination)
