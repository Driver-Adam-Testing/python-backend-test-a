from uuid import UUID

from database.models_v2 import Node
from fastapi import APIRouter, HTTPException
from modal import Function
from modal.functions import FunctionCall
from pydantic import BaseModel, Field, model_validator
from shared.interfaces.agents.pipeline_configuration import (
    DataScope,
    PipelineInput,
    PipelineResponse,
    PipelineStepConfiguration,
    PipelineStepType,
)
from shared.interfaces.request import DriverModalBatchRequest
from shared.interfaces.response import DriverModalResponse
from shared.pipelines.agents.execute import execute_sequence
from sqlmodel import select

from app.api.auth import ContentEditorPermission, ContentReadonlyPermission, UserToken
from app.api.session import CurrentSession

router = APIRouter()


class AgentRunRequest(BaseModel):
    steps: list[PipelineStepConfiguration] = Field(
        default_factory=lambda: [
            PipelineStepConfiguration(step_type=PipelineStepType.DEFAULT)
        ]
    )
    node_ids: list[UUID] | None = None
    page_node_id: UUID | None = None

    @model_validator(mode="before")
    def check_node_ids(cls, values: any) -> any:
        node_ids, page_node_id = values.get("node_ids"), values.get("page_node_id")
        if not node_ids and not page_node_id:
            raise ValueError("Either node_ids or page_node_id must be provided.")
        if node_ids and page_node_id:
            raise ValueError("Only one of node_ids or page_node_id should be provided.")
        return values


@router.post(
    "/",
    summary="Start a modal instance of the execute Agent Sequence",
    dependencies=[ContentEditorPermission],
)
def execute_agent_sequence(
    user: UserToken, session: CurrentSession, input: AgentRunRequest
) -> PipelineResponse:
    # Initialize nodes list
    nodes = []

    # Validate and collect nodes from node_ids
    if input.node_ids:
        nodes = session.exec(select(Node).where(Node.id.in_(input.node_ids))).all()
        if not all(
            node.version.primary_asset.organization_id == user.organization_id
            for node in nodes
        ):
            raise HTTPException(
                status_code=403,
                detail="One or more node_ids are not in the organization.",
            )

    # Validate and collect nodes from page_node_id
    if input.page_node_id:
        page_node = session.exec(
            select(Node).where(Node.id == input.page_node_id)
        ).one_or_none()
        if (
            not page_node
            or page_node.version.primary_asset.organization_id != user.organization_id
        ):
            raise HTTPException(
                status_code=403, detail="page_node_id is not in the organization."
            )

        # Collect nodes from page_node's document sources
        document_source_nodes = session.exec(
            select(Node).where(
                Node.id.in_([source.id for source in page_node.documentsources])
            )
        ).all()
        nodes.extend(document_source_nodes)

    # Create PipelineInput with collected nodes
    pipeline_input = PipelineInput(
        steps=input.steps,
        scope=DataScope(
            nodes=nodes,
        ),
    )

    return execute_sequence(pipeline_input)


@router.post(
    "/async",
    summary="Start a modal instance of the execute Agent Sequence",
    dependencies=[ContentReadonlyPermission],
)
def execute_agent_sequence_modal_async(
    user: UserToken, input: PipelineInput, session: CurrentSession
) -> DriverModalResponse:
    input.scope.organization_id = user.organization_id
    input.scope.user_id = user.user_id
    modal_function = Function.lookup("agent", "run")
    instance = modal_function.spawn(input)
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
    user: UserToken, input: PipelineInput
) -> PipelineResponse:
    input.scope.organization_id = user.organization_id
    modal_function = Function.lookup("agent", "run")
    result = modal_function.remote(input)
    return result
