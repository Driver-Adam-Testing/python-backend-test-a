import asyncio
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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

from app.api.auth import (
    User,
    verify_token,
)

router = APIRouter()


class ChatSetupRequest(BaseModel):
    node_ids: list[UUID]


@router.websocket("/websocket")
async def chat_websocket(websocket: WebSocket) -> None:
    start_time = datetime.now()
    print("Chat websocket connected at", start_time)
    await websocket.accept()

    auth_header = websocket.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=4401)  # 4401 = Unauthorized in WS context
        return

    token = auth_header[len("Bearer ") :]
    try:
        payload = verify_token(token)
    except Exception as e:
        await websocket.send_text(f"Unauthorized: {e.detail}")
        await websocket.close()
        return

    user = User(**payload)
    organization_id = user.organization_id

    try:
        setup_text = await websocket.receive_text()
        setup_message = ChatSetupRequest(**json.loads(setup_text))
    except WebSocketDisconnect:
        print("Client disconnected before sending setup data")
        return

    message_history = LlmMessageHistory()
    message_history.add_message(OverviewOfDriverMessage())
    message_history.add_message(HowDriverWorksMessage())
    message_history.add_message(ContentStructureMessage())
    message_history.add_message(ChatContextMessage())
    message_history.add_message(DriverApplicationMessage())

    try:
        while True:
            user_message_text = await websocket.receive_text()
            if user_message_text == "KEEP_ALIVE":
                continue

            user_message = LlmMessage(
                message_kind=MessageKind.USER, content=user_message_text
            )
            message_history.add_message(user_message)

            async for chunk in run_chat_pipeline(
                message_history=message_history,
                datasource=DataSource.from_node_ids(
                    setup_message.node_ids, organization_id=organization_id
                ),
            ):
                if isinstance(chunk, str):
                    await websocket.send_text(chunk)
                else:
                    message_history.add_message(chunk)
                await asyncio.sleep(0.01)  # Add a small sleep to prevent 100% CPU usage
    except WebSocketDisconnect:
        print(
            "Chat websocket disconnected at",
            datetime.now(),
            "open for",
            datetime.now() - start_time,
        )
        print("Client disconnected during pipeline")
