from collections.abc import Callable
from enum import Enum
from uuid import UUID

import modal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3.app.pipelines import (
    InlineEditPipelineRequest,
    InlineEditPipelineResponse,
    PipelineResponse,
    ReformatPipelineRequest,
    SmartInstructionPipelineRequest,
)
from shared.v3.app.static.enums.format_kinds import FormatKind

from app.api.auth import (
    ContentEditorPermission,
    UserToken,
)

router = APIRouter()


class InlineEditHttpRequest(BaseModel):
    prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    cursor_selection: str
    node_ids: list[UUID]
    remote_execution: bool = True
    stream: bool = True


@router.post(
    "/inline_edit",
    summary="Perform inline editing",
    dependencies=[ContentEditorPermission],
)
async def inline_edit(
    user: UserToken,
    input: InlineEditHttpRequest,
) -> InlineEditPipelineResponse | None:
    """
    Perform inline editing on the selected text.
    """
    parsed_input = InlineEditPipelineRequest(
        user_prompt=input.prompt,
        page_content_before_cursor=input.page_content_before_cursor,
        page_content_after_cursor=input.page_content_after_cursor,
        node_ids=input.node_ids,
        organization_id=user.organization_id,
        cursor_selection=input.cursor_selection,
        user_id=user.user_id,
    )

    if input.stream:
        print(f"Stream: {input.stream}")
        if input.remote_execution:
            return StreamingResponse(
                modal.Function.lookup("generation", "inline_edit_stream").remote_gen(
                    parsed_input.model_dump()
                ),
                media_type="text/event-stream",
            )
        else:
            return StreamingResponse(
                parsed_input.stream(),
                media_type="text/event-stream",
            )
    else:
        if input.remote_execution:
            return modal.Function.lookup("generation", "inline_edit_run").remote(
                parsed_input.model_dump()
            )
        else:
            return parsed_input.run()


@router.get(
    "/attach/{call_id}",
    summary="Attach to modal",
    dependencies=[ContentEditorPermission],
)
def attach_to_modal(user: UserToken, call_id: str, stream: bool = True) -> None:
    function_call = modal.FunctionCall.from_id(call_id, is_generator=stream)
    if stream:
        return StreamingResponse(
            function_call.get_gen(),
            media_type="text/event-stream",
        )
    else:
        return function_call.get()


class PipelineKind(str, Enum):
    INLINE_EDIT = "INLINE_EDIT"
    SMART_INSTRUCTION = "SMART_INSTRUCTION"
    REFORMAT = "REFORMAT"
    CHAT = "CHAT"


class ExecutionType(str, Enum):
    REMOTE_ASYNC = "REMOTE_ASYNC"
    REMOTE_SYNC = "REMOTE_SYNC"
    LOCAL = "LOCAL"


class RemoteFunctions(str, Enum):
    INLINE_EDIT_RUN = "inline_edit_run"
    INLINE_EDIT_STREAM = "inline_edit_stream"
    SMART_INSTRUCTION_RUN = "smart_instruction_run"
    SMART_INSTRUCTION_STREAM = "smart_instruction_stream"
    REFORMAT_RUN = "reformat_run"
    REFORMAT_STREAM = "reformat_stream"
    CHAT_RUN = "chat_run"
    CHAT_STREAM = "chat_stream"


class GenerateHttpRequest(BaseModel):
    prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    cursor_selection: str
    node_ids: list[UUID]
    format_kind: FormatKind = FormatKind.ANY
    stream: bool = True
    pipeline_kind: PipelineKind = PipelineKind.CHAT
    execution_type: ExecutionType = ExecutionType.REMOTE_ASYNC


class AsyncCallResponse(BaseModel):
    llm_session_id: UUID
    remote_execution_id: str


# → Which request model to build for each PipelineKind
_PIPELINE_BUILDERS: dict[
    PipelineKind, Callable[[GenerateHttpRequest, UserToken], BaseModel]
] = {
    PipelineKind.INLINE_EDIT: lambda req, user: InlineEditPipelineRequest(
        user_prompt=req.prompt,
        page_content_before_cursor=req.page_content_before_cursor,
        page_content_after_cursor=req.page_content_after_cursor,
        cursor_selection=req.cursor_selection,
        node_ids=req.node_ids,
        organization_id=user.organization_id,
        user_id=user.user_id,
    ),
    PipelineKind.SMART_INSTRUCTION: lambda req, user: SmartInstructionPipelineRequest(
        user_prompt=req.prompt,
        page_content_before_cursor=req.page_content_before_cursor,
        page_content_after_cursor=req.page_content_after_cursor,
        format_kind=req.format_kind,
        node_ids=req.node_ids,
        organization_id=user.organization_id,
        user_id=user.user_id,
    ),
    PipelineKind.REFORMAT: lambda req, user: ReformatPipelineRequest(
        cursor_selection=req.cursor_selection,
        format_kind=req.format_kind,
        node_ids=req.node_ids,
        organization_id=user.organization_id,
        user_id=user.user_id,
    ),
    # PipelineKind.CHAT     : lambda req, user: ...,
}

_REMOTE_FUNCTION_NAMES: dict[tuple[PipelineKind, bool], str] = {
    (PipelineKind.CHAT, True): "chat_stream",
    (PipelineKind.CHAT, False): "chat_run",
    (PipelineKind.INLINE_EDIT, True): "inline_edit_stream",
    (PipelineKind.INLINE_EDIT, False): "inline_edit_run",
    (PipelineKind.SMART_INSTRUCTION, True): "smart_instruction_stream",
    (PipelineKind.SMART_INSTRUCTION, False): "smart_instruction_run",
    (PipelineKind.REFORMAT, True): "reformat_stream",
    (PipelineKind.REFORMAT, False): "reformat_run",
}


@router.post(
    "/",
    summary="Generate content",
    dependencies=[ContentEditorPermission],
)
async def generate(
    user: UserToken, input: GenerateHttpRequest
) -> AsyncCallResponse | PipelineResponse | None:
    """
    Generate content based on the prompt and the context.
    """

    parsed_input = _PIPELINE_BUILDERS[input.pipeline_kind](input, user)

    if input.execution_type is ExecutionType.LOCAL:
        return (
            StreamingResponse(
                parsed_input.stream() if input.stream else parsed_input.run(),
                media_type="text/event-stream",
            )
            if input.stream
            else parsed_input.run()
        )
    remote_function_name = _REMOTE_FUNCTION_NAMES[(input.pipeline_kind, input.stream)]
    fn = modal.Function.from_name("generation", remote_function_name)
    if input.stream:
        return StreamingResponse(
            fn.remote_gen(parsed_input.model_dump()),
            media_type="text/event-stream",
        )
    else:
        if input.execution_type is ExecutionType.REMOTE_ASYNC:
            return fn.spawn(parsed_input.model_dump())
        else:
            return fn.remote(parsed_input.model_dump())
