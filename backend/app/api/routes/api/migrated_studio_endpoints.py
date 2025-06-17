from app.api.auth import ApiKeyToken
from app.api.routes.v2.chat import ChatHttpRequest, create_streaming_post
from app.api.session import CurrentSession
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/chat")
def tmp_chat(
    user: ApiKeyToken, session: CurrentSession, payload: ChatHttpRequest
) -> StreamingResponse:
    return create_streaming_post(session, user, payload)


# @router.get("/tmp/tags", response_model=ListWithCount[TagDetailRead])
# def tmp_list_tags(
#     request: Request,
#     session: CurrentSession,
#     user: ApiKeyToken,
#     pagination: Pagination,
# ) -> ListWithCount[TagDetailRead]:
#     return list_tags(user, session, pagination)


# @router.get("/tmp/node/tags")
# def tmp_list_node_tags(
#     user: ApiKeyToken, session: CurrentSession, node_id: uuid.UUID
# ) -> list[str]:
#     return list_tags(user, session, node_id)
