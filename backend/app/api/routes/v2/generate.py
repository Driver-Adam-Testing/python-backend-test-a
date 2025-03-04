from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from shared.interfaces.agents.block_kind import BlockKind
from shared.interfaces.request import DriverModalBatchRequest

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession

router = APIRouter()


class SmartInstructionRequest(BaseModel):
    prompt: str
    block_kind: BlockKind
    page_content_before: str
    page_content_after: str
    node_ids: list[UUID]


class InlineEditRequest(BaseModel):
    prompt: str
    generation_context: dict
    selected_text: str
    page_content_before: str
    page_content_after: str
    node_ids: list[UUID]


class ChatRequest(BaseModel):
    prompt: str
    node_ids: list[UUID]


@router.post(
    "/generate/smart_instruction",
    summary="Generate smart instruction",
    dependencies=[ContentEditorPermission],
)
def generate_smart_instruction(
    user: UserToken, session: CurrentSession, input: SmartInstructionRequest
) -> bool:
    return True


@router.post(
    "/generate/inline_edit",
    summary="Generate inline edit",
    dependencies=[ContentEditorPermission],
)
def generate_inline_edit(
    user: UserToken, session: CurrentSession, input: InlineEditRequest
) -> bool:
    return True


@router.post(
    "/generate/chat",
    summary="Generate chat response",
    dependencies=[ContentEditorPermission],
)
def generate_chat(user: UserToken, session: CurrentSession, input: ChatRequest) -> bool:
    return True


@router.post(
    "/generate/smart_instruction/async",
    summary="Generate smart instruction asynchronously",
    dependencies=[ContentReadonlyPermission],
)
def generate_smart_instruction_async(
    user: UserToken, input: SmartInstructionRequest, session: CurrentSession
) -> bool:
    return True


@router.post(
    "/generate/inline_edit/async",
    summary="Generate inline edit asynchronously",
    dependencies=[ContentReadonlyPermission],
)
def generate_inline_edit_async(
    user: UserToken, input: InlineEditRequest, session: CurrentSession
) -> bool:
    return True


@router.post(
    "/generate/chat/async",
    summary="Generate chat response asynchronously",
    dependencies=[ContentReadonlyPermission],
)
def generate_chat_async(
    user: UserToken, input: ChatRequest, session: CurrentSession
) -> bool:
    return True


@router.get("/generate/async/{call_id}", dependencies=[ContentReadonlyPermission])
def get_generation_results(user: UserToken, call_id: str) -> bool:
    return True


class BatchInput(BaseModel):
    call_ids: list[str]


@router.post("/generate/async/batch", dependencies=[ContentReadonlyPermission])
def get_batch_generation_results(
    user: UserToken, input: DriverModalBatchRequest
) -> bool:
    return True
