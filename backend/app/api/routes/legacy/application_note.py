import json
from enum import Enum

import strawberry
from modal.functions import FunctionCall
from sqlmodel import Session

from app.api.routes.legacy.orm_ops import get_derived_content_by_id
from app.api.routes.legacy.scalars import JSON
from app.core.logger import logger


@strawberry.type
class ApplicationNoteResponse:
    id: str
    status: str
    prompt: str | None = None
    name: str | None = None
    content: JSON | None = None  # type: ignore
    description: str | None = None
    metadata: dict
    generation_timestamp: str | None = None


def get_application_note(id: str, session: Session, organization_id: str):
    maybe_doc = get_derived_content_by_id(session, id, organization_id)

    if not maybe_doc:
        logger.error("Document not found")
        return None

    doc = maybe_doc
    parsed_content = None
    try:
        parsed_content = json.loads(str(doc.content))
    except json.JSONDecodeError as e:
        logger.warning(f"[ParseError]: {doc.id} - {e.msg}")
        return None

    if parsed_content:
        note = ApplicationNoteResponse(
            id=str(doc.id),
            status=doc.status,
            prompt=parsed_content.get("description", ""),
            name=parsed_content.get("name", ""),
            content=parsed_content.get("content", ""),
            description=parsed_content.get("description", ""),
            metadata=doc.dc_metadata,  # type: ignore
            generation_timestamp=doc.created_at.isoformat() if doc.created_at else None,
        )
        return note
    else:
        logger.error(f"[ParseError]: Application note {doc.id} has invalid content.")
        return None


@strawberry.type
class ApplicationNoteEditResponse:
    call_id: str
    content: str | None
    status: str


class ContentStatus(Enum):
    GENERATING = "generating"
    GENERATION_COMPLETE = "generation-complete"
    GENERATION_ERROR = "generation-error"


async def application_note_edit(call_id: str) -> ApplicationNoteEditResponse:
    function_call = FunctionCall.from_id(call_id)
    try:
        result = function_call.get(timeout=0)
    except TimeoutError:
        return ApplicationNoteEditResponse(
            call_id=call_id, status=ContentStatus.GENERATING.value, content=""
        )
    return ApplicationNoteEditResponse(
        call_id=call_id,
        status=ContentStatus.GENERATION_COMPLETE.value,
        content=result["content"],
    )
