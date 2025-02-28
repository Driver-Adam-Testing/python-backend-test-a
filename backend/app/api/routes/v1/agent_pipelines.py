import uuid
from uuid import UUID

from fastapi import APIRouter
from modal import Function
from modal.functions import FunctionCall
from pydantic import BaseModel, Field
from shared.interfaces.agents.block_kind import BlockKind
from shared.interfaces.agents.pipeline_configuration import (
    DataScope,
    PipelineInput,
    PipelineResponse,
    PipelineStepConfiguration,
    PipelineStepResponse,
    PipelineStepType,
    PromptWithContext,
)
from shared.interfaces.request import DriverModalBatchRequest
from shared.interfaces.response import DriverModalResponse
from shared.pipelines.agents.execute import execute_sequence
from shared.pipelines.block_kind_pipelines.code import execute_code_block_agent
from shared.pipelines.block_kind_pipelines.diagram import execute_diagram_block_agent
from shared.pipelines.block_kind_pipelines.list import execute_list_block_agent
from shared.pipelines.block_kind_pipelines.table import execute_table_block_agent
from shared.prompts.block_kind.block_kind_any import BlockKindCopyEditorAny
from shared.prompts.block_kind.block_kind_code import BlockKindCopyEditorCodeBlock
from shared.prompts.block_kind.block_kind_diagram import BlockKindCopyEditorDiagram
from shared.prompts.block_kind.block_kind_list import BlockKindCopyEditorList
from shared.prompts.block_kind.block_kind_table import BlockKindCopyEditorTable
from shared.prompts.block_kind.block_kind_text import BlockKindCopyEditorText

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession

router = APIRouter()


class AgentRunRequest(PromptWithContext):
    steps: list[PipelineStepConfiguration] = Field(
        default_factory=lambda: [
            PipelineStepConfiguration(step_type=PipelineStepType.DEFAULT)
        ]
    )
    node_ids: list[UUID] | None = None
    block_kind: BlockKind | None = None


@router.post(
    "/dep",
    summary="Start a modal instance of the execute Agent Sequence",
    dependencies=[ContentEditorPermission],
)
def execute_agent_sequence(
    user: UserToken, session: CurrentSession, input: AgentRunRequest
) -> PipelineResponse:
    # TODO: authorize node_ids
    block_kind_to_response_format = {
        BlockKind.TEXT: BlockKindCopyEditorText,
        BlockKind.LIST: BlockKindCopyEditorList,
        BlockKind.ANY: BlockKindCopyEditorAny,
        BlockKind.CODE: BlockKindCopyEditorCodeBlock,
        BlockKind.DIAGRAM: BlockKindCopyEditorDiagram,
        BlockKind.TABLE: BlockKindCopyEditorTable,
    }
    response_format = block_kind_to_response_format.get(
        input.block_kind or BlockKind.ANY, BlockKindCopyEditorAny
    )

    pipeline_input = PipelineInput(
        prompt=input.prompt,
        context=input.context,
        steps=input.steps,
        scope=DataScope(
            node_ids=input.node_ids,
            organization_id=user.organization_id,
            user_id=user.subject,
        ),
        response_format=response_format,
    )
    if input.block_kind == BlockKind.LIST:
        return execute_list_block_agent(pipeline_input)
    elif input.block_kind == BlockKind.TABLE:
        return execute_table_block_agent(pipeline_input)
    elif input.block_kind == BlockKind.DIAGRAM:
        return execute_diagram_block_agent(pipeline_input)
    elif input.block_kind == BlockKind.CODE:
        return execute_code_block_agent(pipeline_input)
    return execute_sequence(pipeline_input)


@router.post(
    "/async",
    summary="Start a modal instance of the execute Agent Sequence",
    dependencies=[ContentReadonlyPermission],
)
def execute_agent_sequence_modal_async(
    user: UserToken, input: AgentRunRequest, session: CurrentSession
) -> DriverModalResponse:
    block_kind_to_response_format = {
        BlockKind.TEXT: BlockKindCopyEditorText,
        BlockKind.LIST: BlockKindCopyEditorList,
        BlockKind.ANY: BlockKindCopyEditorAny,
        BlockKind.CODE: BlockKindCopyEditorCodeBlock,
        BlockKind.DIAGRAM: BlockKindCopyEditorDiagram,
        BlockKind.TABLE: BlockKindCopyEditorTable,
    }
    response_format = block_kind_to_response_format.get(
        input.block_kind or BlockKind.ANY, BlockKindCopyEditorAny
    )

    pipeline_input = PipelineInput(
        prompt=input.prompt,
        context=input.context,
        steps=input.steps,
        scope=DataScope(
            node_ids=input.node_ids,
            organization_id=user.organization_id,
            user_id=user.subject,
        ),
        response_format=response_format,
        block_kind=input.block_kind,
    )
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(pipeline_input)
    return DriverModalResponse(call_id=instance.object_id)


@router.get("/async/{call_id}", dependencies=[ContentReadonlyPermission])
def get_execution_results(user: UserToken, call_id: str) -> PipelineResponse:
    function_call = FunctionCall.from_id(call_id)
    result = function_call.get(timeout=0)
    return result


class BatchInput(BaseModel):
    call_ids: list[str]


# TODO: this url is poorly formatted. used to keep the same as instructions for rapid development
@router.post("/async/batch", dependencies=[ContentReadonlyPermission])
def get_batch_execution_results(
    user: UserToken, input: DriverModalBatchRequest
) -> dict:
    results = {}
    for call_id in input.call_ids:
        function_call = FunctionCall.from_id(call_id)
        # TODO: don't transform the output
        try:
            result = function_call.get(timeout=0)
            results[call_id] = {
                "call_id": call_id,
                "status": "completed",
                "response": result,
                "error": "",
            }
        except TimeoutError:
            results[call_id] = {
                "call_id": call_id,
                "status": "running",
                "response": None,
                "error": "",
            }
        except Exception as e:
            results[call_id] = {
                "call_id": call_id,
                "status": "expired",
                "response": None,
                "error": str(e),
            }
    return results


@router.post(
    "/sync",
    summary="Start a modal instance of the execute Agent Sequence",
    dependencies=[ContentReadonlyPermission],
)
def execute_agent_sequence_modal_sync(
    user: UserToken, input: AgentRunRequest
) -> PipelineResponse:
    # Transform AgentRunRequest to PipelineInput
    pipeline_input = PipelineInput(
        steps=input.steps,
        scope=DataScope(
            node_ids=input.node_ids,
            organization_id=user.organization_id,
            user_id=user.subject,
        ),
    )

    modal_function = Function.lookup("agent", "run")
    result = modal_function.remote(pipeline_input)
    return result


@router.post(
    "/",
    summary="Execute Agent Sequence with V3",
    dependencies=[ContentEditorPermission],
)
def execute_agent_sequence_v3(
    user: UserToken, session: CurrentSession, input: AgentRunRequest
) -> PipelineResponse:
    from shared.v3.app.pipelines.smart_instruction import run_smart_instruction

    result = run_smart_instruction(
        user_prompt=input.prompt,
        text_after_instruction=input.context["after_selected_text"],
        text_before_instruction=input.context["before_selected_text"],
        datascope=DataScope(
            node_ids=input.node_ids,
            organization_id=user.organization_id,
            user_id=user.subject,
        ),
    )

    return PipelineResponse(
        step_responses=[
            PipelineStepResponse(agent_id=uuid.uuid4(), agent_result=str(result))
        ],
        final_result=str(result["final_response"]),
    )
