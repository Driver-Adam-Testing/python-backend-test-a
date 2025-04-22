from uuid import UUID

import modal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3.app.pipelines import InlineEditPipelineInput, InlineEditPipelineResponse

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
    use_modal: bool = True
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
    parsed_input = InlineEditPipelineInput(
        user_prompt=input.prompt,
        page_content_before_cursor=input.page_content_before_cursor,
        page_content_after_cursor=input.page_content_after_cursor,
        node_ids=input.node_ids,
        organization_id=user.organization_id,
        selected_text=input.cursor_selection,
        user_id=user.user_id,
    )

    if input.stream:
        print(f"Stream: {input.stream}")
        if input.use_modal:
            return StreamingResponse(
                modal.Function.lookup(
                    "generation", "inline_edit_stream", environment_name="neil"
                ).remote_gen(parsed_input.model_dump()),
                media_type="text/event-stream",
            )
        else:
            return parsed_input.stream()
    else:
        if input.use_modal:
            return modal.Function.lookup(
                "generation", "inline_edit_run", environment_name="neil"
            ).remote(parsed_input.model_dump())
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
