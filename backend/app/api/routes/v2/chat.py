import json
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
    # TODO: Do this in a Datasource to verify the node_ids can be accessed by the page and that the org_id is correct
    if source_node_ids is None and page_node_id is not None:
        source_node_ids = session.exec(
            select(DocumentSource.source_node_id).where(
                DocumentSource.page_node_id == page_node_id
            )
        ).all()
    datasource = DataSource.from_node_ids(
        node_ids=source_node_ids,
        organization_id=user.organization_id,
    )
    if llm_session_id is None:
        llm_session = RuntimeLlmSession(
            id=llm_session_id,
            user_id=user.user_id,
            organization_id=user.organization_id,
            source_node_ids_str=json.dumps(source_node_ids, cls=UUIDEncoder),
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
    else:
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

    chat_message_history.add_message(
        LlmMessage(message_kind=MessageKind.USER, content=payload.user_prompt)
    )
    print([m.message_kind for m in chat_message_history.messages])
    return StreamingResponse(
        run_chat_pipeline(
            llm_session_id,
            chat_message_history,
            datasource,
        ),
        media_type="text/plain",
    )
