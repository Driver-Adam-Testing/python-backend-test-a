from app.api.auth import ApiKeyToken
from app.api.routes.legacy.document_set import get_document_set
from app.api.routes.legacy.tree import get_codebase_tree
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
async def create_streaming_post_endpoint(
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
def get_primary_assets_endpoint(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    pagination: Pagination,
    tag_ids: str | None = None,
) -> ListWithCount[PrimaryAssetDetailRead]:
    return _list_primary_assets(request, session, user, pagination, tag_ids)


@router.get("/contents", response_model=ListWithCount[ContentDetailRead])
def get_contents_endpoint(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    pagination: Pagination,
) -> ListWithCount[ContentDetailRead]:
    return _list_contents(request, session, user, pagination)


@router.get("/tree", response_model=list[dict])
def get_tree_endpoint(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    codebaseId: str | None = None,
    workspaceId: str | None = None,
    versionId: str | None = None,
) -> list[dict]:
    tree = get_codebase_tree(
        session=session,
        organization_id=user.organization_id,
        version_id=versionId,
    )

    return [
        {
            "id": node.id,
            "name": node.name,
            "path": node.path,
            "kind": node.kind,
            "children": node.children,
        }
        for node in tree
    ]


@router.get("/document_set", response_model=dict)
def get_document_set_endpoint(
    request: Request,
    session: CurrentSession,
    user: ApiKeyToken,
    primaryAssetId: str,
    path: str,
    versionId: str,
) -> dict:
    document_set = get_document_set(
        node_kind="THIS ISNT EVEN IMPLEMENTED",
        path=path,
        primary_asset_id=primaryAssetId,
        organization_id=user.organization_id,
        session=session,
        fetch_code_content=True,
        version_id=versionId,
    )
    return {
        "source_content_id": document_set.source_content_id,
        "architecture": document_set.architecture,
        "architecture_document": document_set.architecture_document,
        "long": document_set.long,
        "long_document": document_set.long_document,
        "short": document_set.short,
        "quickstart": document_set.quickstart,
        "chunk_descriptions": document_set.chunk_descriptions,
        "code": document_set.code,
        "toplevel": document_set.toplevel,
        "application_notes": document_set.application_notes,
    }
