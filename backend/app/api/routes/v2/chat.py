import json
from uuid import UUID

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
from shared.v3.utils.encoder import UUIDEncoder
from sqlmodel import select

from app.api.auth import (
    UserToken,
)
from app.api.session import CurrentSession

router = APIRouter()


class ChatRequest(BaseModel):
    user_prompt: str
    source_node_ids: list[UUID] | None = None
    page_node_id: UUID | None = None
    llm_session_id: UUID | None = None


def get_datasource(
    source_node_ids: list[UUID] | None,
    page_node_id: UUID | None,
    llm_session: RuntimeLlmSession | None,
    user: UserToken,
) -> DataSource:
    if source_node_ids:
        return DataSource.from_node_ids(source_node_ids, user.organization_id)
    if page_node_id:
        return DataSource.from_page_id(page_node_id, user.organization_id)
    if llm_session:
        return DataSource.from_node_ids(
            json.loads(llm_session.source_node_ids_str), user.organization_id
        )
    raise Exception("Please provide either a page_node_id or source_node_ids.")


@router.post("/")
async def create_streaming_post(
    session: CurrentSession,
    user: UserToken,
    payload: ChatRequest,
) -> StreamingResponse:
    source_node_ids: list[UUID] | None = payload.source_node_ids
    page_node_id: UUID | None = payload.page_node_id
    llm_session_id: UUID | None = payload.llm_session_id
    chat_message_history: LlmMessageHistory | None = None
    llm_session: RuntimeLlmSession | None = None
    chat_message_history_id: UUID | None = None

    if llm_session_id:
        llm_session = session.exec(
            select(RuntimeLlmSession).where(RuntimeLlmSession.id == llm_session_id)
        ).first()
        if llm_session is None:
            raise Exception(f"Failed to find llm session {llm_session_id}")
        chat_message_history_id = session.exec(
            select(RuntimeLlmMessageHistory.id).where(
                RuntimeLlmMessageHistory.llm_session_id == llm_session_id,
                RuntimeLlmMessageHistory.pipeline_kind == LlmPipelineKind.CHAT,
            )
        ).first()
        if chat_message_history_id is None:
            raise Exception(
                f"Failed to find chat message history for llm session {llm_session_id}"
            )
        chat_message_history = LlmMessageHistory.from_db(
            message_history_id=chat_message_history_id
        )

    datasource = get_datasource(source_node_ids, page_node_id, llm_session, user)

    if llm_session_id is None:
        llm_session = RuntimeLlmSession(
            id=llm_session_id,
            user_id=user.user_id,
            organization_id=user.organization_id,
            source_node_ids_str=json.dumps(datasource.node_ids, cls=UUIDEncoder),
            page_node_id=page_node_id,
        )
        session.add(llm_session)
        session.commit()
        session.refresh(llm_session)
        llm_session_id = llm_session.id
        chat_message_history = LlmMessageHistory(
            messages=[
                DriverApplicationMessage(),
                ContentStructureMessage(),
                HowDriverWorksMessage(),
                OverviewOfDriverMessage(),
                ChatContextMessage(),
            ],
            llm_session_id=llm_session_id,
            pipeline_kind=LlmPipelineKind.CHAT,
        )
        chat_message_history_id = chat_message_history.id
    chat_message_history.add_message(
        LlmMessage(message_kind=MessageKind.USER, content=payload.user_prompt)
    )
    return StreamingResponse(
        run_chat_pipeline(
            llm_session_id,
            chat_message_history,
            datasource,
        ),
        media_type="text/event-stream",
    )
