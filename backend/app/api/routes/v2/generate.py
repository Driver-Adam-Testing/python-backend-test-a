from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from shared.interfaces.agents.block_kind import BlockKind
from shared.v3.utils.datasource import DataSource

from app.api.auth import ContentEditorPermission, UserToken
from app.api.session import CurrentSession

router = APIRouter()


class SmartInstructionRequest(BaseModel):
    prompt: str
    block_kind: BlockKind
    page_content_before_cursor: str
    page_content_after_cursor: str
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
    "/smart_instruction",
    summary="Generate smart instruction",
    dependencies=[ContentEditorPermission],
)
def generate_smart_instruction(
    user: UserToken, session: CurrentSession, input: SmartInstructionRequest
) -> bool:
    from shared.v3.app.pipelines.smart_instruction import run_smart_instruction

    return run_smart_instruction(
        user_prompt=input.prompt,
        text_before_instruction=input.page_content_before_cursor,
        text_after_instruction=input.page_content_after_cursor,
        datasource=DataSource.from_node_ids(input.node_ids),
        block_kind=input.block_kind,
    )


@router.post(
    "/inline_edit",
    summary="Generate inline edit",
    dependencies=[ContentEditorPermission],
)
def generate_inline_edit(
    user: UserToken, session: CurrentSession, input: InlineEditRequest
) -> bool:
    return True


@router.post(
    "/chat",
    summary="Generate chat response",
)
def generate_chat(user: UserToken, session: CurrentSession, input: ChatRequest) -> bool:
    return True


# @router.post(
#     "/generate/smart_instruction/async",
#     summary="Generate smart instruction asynchronously",
#     dependencies=[ContentReadonlyPermission],
# )
# def generate_smart_instruction_async(
#     user: UserToken, input: SmartInstructionRequest, session: CurrentSession
# ) -> bool:
#     return True


# @router.post(
#     "/generate/inline_edit/async",
#     summary="Generate inline edit asynchronously",
#     dependencies=[ContentReadonlyPermission],
# )
# def generate_inline_edit_async(
#     user: UserToken, input: InlineEditRequest, session: CurrentSession
# ) -> bool:
#     return True


# @router.post(
#     "/generate/chat/async",
#     summary="Generate chat response asynchronously",
#     dependencies=[ContentReadonlyPermission],
# )
# def generate_chat_async(
#     user: UserToken, input: ChatRequest, session: CurrentSession
# ) -> bool:
#     return True


# @router.get("/generate/async/{call_id}", dependencies=[ContentReadonlyPermission])
# def get_generation_results(user: UserToken, call_id: str) -> bool:
#     return True


# class BatchResultsInput(BaseModel):
#     call_ids: list[str]


# @router.post("/generate/async/batch_results", dependencies=[ContentReadonlyPermission])
# def get_batch_generation_results(
#     user: UserToken, input: DriverModalBatchRequest
# ) -> bool:
#     return True
