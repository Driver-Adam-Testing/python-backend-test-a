from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from shared.interfaces.agents.block_kind import BlockKind
from shared.v3.app.pipelines.inline_edit import (
    run_inline_edit,
)
from shared.v3.app.pipelines.smart_instruction import (
    SmartInstructionPipelineResponse,
    run_smart_instruction,
)
from shared.v3.utils.datasource import DataSource
from shared.v3.utils.references import Reference

from app.api.auth import (
    ContentEditorPermission,
    UserToken,
)

router = APIRouter()


class SmartInstructionRequest(BaseModel):
    prompt: str
    block_kind: BlockKind
    page_content_before_cursor: str
    page_content_after_cursor: str
    node_ids: list[UUID]


class InlineEditRequest(BaseModel):
    prompt: str
    selected_text: str
    page_content_before: str
    page_content_after: str
    node_ids: list[UUID]


class InlineEditResponse(BaseModel):
    final_response: str
    references: list[Reference]


@router.post(
    "/smart_instruction",
    summary="Generate smart instruction",
    dependencies=[ContentEditorPermission],
)
def generate_smart_instruction(
    user: UserToken,
    input: SmartInstructionRequest,
) -> SmartInstructionPipelineResponse:
    return run_smart_instruction(
        user_prompt=input.prompt,
        text_before_instruction=input.page_content_before_cursor,
        text_after_instruction=input.page_content_after_cursor,
        datasource=DataSource.from_node_ids(
            input.node_ids, organization_id=user.organization_id
        ),
        block_kind=input.block_kind,
    )


@router.post(
    "/inline_edit",
    summary="Perform inline editing",
    dependencies=[ContentEditorPermission],
)
def inline_edit(
    user: UserToken,
    input: InlineEditRequest,
) -> InlineEditResponse:
    """
    Perform inline editing on the selected text.
    """

    return run_inline_edit(
        user_prompt=input.prompt,
        text_before_instruction=input.page_content_before,
        text_after_instruction=input.page_content_after,
        datasource=DataSource.from_node_ids(
            input.node_ids, organization_id=user.organization_id
        ),
        selected_text=input.selected_text,
    )
