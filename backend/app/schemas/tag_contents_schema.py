from typing import Optional
from uuid import UUID
from pydantic import BaseModel

# Pydantic models
class TagContentCreate(BaseModel):
    tag_id: UUID
    content_id: UUID
    include: bool
