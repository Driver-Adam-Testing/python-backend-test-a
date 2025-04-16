from uuid import UUID

import modal
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from shared.v3.app.pipelines import InlineEditPipelineInput, InlineEditPipelineResponse
from shared.v3.utils.datasource import DataSource

from app.api.auth import (
    ContentEditorPermission,
    UserToken,
)

router = APIRouter()


class InlineEditHttpRequest(BaseModel):
    prompt: str
    page_content_before_cursor: str
    page_content_after_cursor: str
    node_ids: list[UUID]
    cursor_selection: str


@router.post(
    "/inline_edit",
    summary="Perform inline editing",
    dependencies=[ContentEditorPermission],
)
def inline_edit(
    user: UserToken,
    input: InlineEditHttpRequest,
) -> InlineEditPipelineResponse:
    """
    Perform inline editing on the selected text.
    """
    response = InlineEditPipelineInput(
        user_prompt=input.prompt,
        page_content_before_cursor=input.page_content_before_cursor,
        page_content_after_cursor=input.page_content_after_cursor,
        datasource=DataSource.from_node_ids(
            input.node_ids, organization_id=user.organization_id
        ),
        selected_text=input.cursor_selection,
    ).run()
    return response


@router.post(
    "/inline_edit_stream",
    summary="stream inline edit",
    dependencies=[ContentEditorPermission],
)
def inline_edit_stream(user: UserToken, input: InlineEditHttpRequest) -> None:
    parsed_input = InlineEditPipelineInput(
        user_prompt=input.prompt,
        page_content_before_cursor=input.page_content_before_cursor,
        page_content_after_cursor=input.page_content_after_cursor,
        node_ids=input.node_ids,
        organization_id=user.organization_id,
        selected_text=input.cursor_selection,
    )
    return StreamingResponse(
        modal.Function.lookup(
            "generation", "inline_edit_stream", environment_name="neil"
        ).remote_gen(parsed_input.model_dump()),
        media_type="text/event-stream",
    )
