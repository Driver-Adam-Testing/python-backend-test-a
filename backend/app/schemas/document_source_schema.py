from typing import Optional
from uuid import UUID
from pydantic import BaseModel

# Pydantic models
class DocumentSourceCreate(BaseModel):
    document_id: UUID
    source_id: UUID
    include: bool
