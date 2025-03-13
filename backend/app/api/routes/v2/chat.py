from uuid import UUID

from database.models_v1 import DocumentSource
from database.models_v2 import RuntimeLlmMessageHistory, RuntimeLlmSession
from database.models_v2_enums import LlmPipelineKind
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3 import LlmMessage, LlmMessageHistory, MessageKind
from shared.v3.app.pipelines.chat import run_chat_pipeline
from shared.v3.app.static.messages.driver_app_messages import (
    ChatContextMessage,
    ContentStructureMessage,
    DriverApplicationMessage,
    HowDriverWorksMessage,
    OverviewOfDriverMessage,
)
from shared.v3.utils.datasource import DataSource
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.auth import (
    UserToken,
)
from app.api.session import CurrentSession

router = APIRouter()


class ChatSetupRequest(BaseModel):
    source_node_ids: list[UUID] | None = None
    page_node_id: UUID | None = None
    llm_session_id: UUID | None = None


@router.post("/")
async def create_streaming_post(
    session: CurrentSession,
    user: UserToken,
    payload: ChatSetupRequest,
) -> StreamingResponse:
    source_node_ids: list[UUID] | None = payload.source_node_ids
    page_node_id: UUID | None = payload.page_node_id
    llm_session_id: UUID | None = payload.llm_session_id
    chat_message_history: LlmMessageHistory | None = None
    llm_session: RuntimeLlmSession | None = None
    # TODO: Do this in a Datasource to verify the node_ids can be accessed by the page and that the org_id is correct
    if source_node_ids is None and page_node_id is not None:
        source_node_ids = session.exec(
            select(DocumentSource.source_node_id).where(
                DocumentSource.page_node_id == page_node_id
            )
        ).all()
    datasource = DataSource.from_node_ids(
        node_ids=source_node_ids, organization_id=user.organization_id
    )
    if llm_session_id:
        llm_session = session.exec(
            select(RuntimeLlmSession)
            .where(RuntimeLlmSession.id == llm_session_id)
            .options(
                selectinload(RuntimeLlmSession.message_histories).selectinload(
                    RuntimeLlmMessageHistory.messages
                ),
            )
        ).first()
    if llm_session is None:
        llm_session = RuntimeLlmSession(
            id=llm_session_id,
            user_id=user.user_id,
            organization_id=user.organization_id,
            node_ids=source_node_ids,
            page_node_id=page_node_id,
        )
        session.add(llm_session)
        session.commit()
        session.refresh(llm_session)
    for message_history in llm_session.message_histories:
        if message_history.pipeline_kind == LlmPipelineKind.CHAT:
            chat_message_history = LlmMessageHistory.from_runtime_llm_message_history(
                message_history
            )
    if chat_message_history is None:
        chat_message_history = LlmMessageHistory(
            llm_session_id=llm_session.id,
            pipeline_kind=LlmPipelineKind.CHAT,
        )
        chat_message_history.add_message(DriverApplicationMessage())
        chat_message_history.add_message(ContentStructureMessage())
        chat_message_history.add_message(ChatContextMessage())
        chat_message_history.add_message(HowDriverWorksMessage())
        chat_message_history.add_message(OverviewOfDriverMessage())
    chat_message_history.add_message(
        LlmMessage(message_kind=MessageKind.USER, content=payload.user_prompt)
    )
    return StreamingResponse(
        run_chat_pipeline(
            chat_message_history,
            datasource,
        ),
        media_type="text/plain",
    )
