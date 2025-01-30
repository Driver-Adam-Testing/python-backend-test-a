from enum import Enum
from uuid import UUID

from database.models_v2 import Node, PrimaryAsset, Version
from fastapi import Body, HTTPException
from pydantic import BaseModel
from shared.interfaces.agents.block_kind import BlockKind
from sqlmodel import select

from app.api.auth import UserToken
from app.api.routes.v2.router import router
from app.api.session import CurrentSession


class Environment(str, Enum):
    CHAT = "chat"
    EDIT = "edit"
    INSERT_INTO_DOCUMENT = "insert_into_document"


class WorkingDocument(BaseModel):
    selected_text: str
    text_before: str
    text_after: str


class GenerateRequest(BaseModel):
    environment: Environment
    prompt: str
    node_ids: list[UUID]
    working_document: WorkingDocument
    block_kind: BlockKind


@router.post("/generate")
def generate_content(
    session: CurrentSession, user: UserToken, request: GenerateRequest = Body(...)
):
    # Verify that all node_ids belong to the user's organization
    nodes = session.exec(
        select(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(Node.id.in_(request.node_ids))
        .where(PrimaryAsset.organization_id == user.organization_id)
    ).all()

    if len(nodes) != len(request.node_ids):
        raise HTTPException(
            status_code=404, detail="One or more nodes not found or not authorized"
        )
    # Placeholder for the actual generation logic
    # You would typically use the request data to perform some operation
    # and return the generated content.
    return {
        "message": "Content generation is not yet implemented.",
        "environment": request.environment,
        "prompt": request.prompt,
        "node_ids": request.node_ids,
        "working_document": request.working_document,
        "block_kind": request.block_kind,
    }
