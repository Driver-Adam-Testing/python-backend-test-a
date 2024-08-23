from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.schemas.tag_contents_schema import TagContentCreate
from app.services.tag_content_service import TagContentService
from app.api.auth import CurrentUser
from app.api.session import CurrentSession
from database.models_v1 import TagContent
router = APIRouter()


@router.post("/", response_model=TagContent)
def create_tag_content(
    session: CurrentSession,
    user: CurrentUser,
    tag_content: TagContentCreate
):
    tag_content_service = TagContentService(session)
    return tag_content_service.create_tag_content(tag_content)



@router.get("/{tag_id}/{content_id}", response_model=TagContent)
def get_tag_content(
    session: CurrentSession,
    user: CurrentUser,
    tag_id: UUID,
    content_id: UUID
):
    tag_content_service = TagContentService(session)
    tag_content = tag_content_service.get_tag_content(tag_id, content_id)
    if not tag_content:
        raise HTTPException(status_code=404, detail="TagContent not found")
    return tag_content

@router.delete("/{tag_id}/{content_id}", response_model=TagContent)
def delete_tag_content(
    session: CurrentSession,
    user: CurrentUser,
    tag_id: UUID,
    content_id: UUID
):
    tag_content_service = TagContentService(session)
    return tag_content_service.delete_tag_content(tag_id, content_id)
