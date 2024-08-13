from typing import Literal, Optional

from pydantic import BaseModel

from app.schemas.content_schema import ListContentResult
from database.models_v1 import Tag

TagType = Literal["tag", "collection"]


class ListTagsInput(BaseModel):
    name: str | None
    type: TagType | None
    limit: int
    offset: int


class NewTagInput(BaseModel):
    name: str
    hex_color: str
    type: TagType


class EditTagInput(BaseModel):
    name: Optional[str] = None
    hex_color: Optional[str] = None


class ListTagsResults(BaseModel):
    results: list[Tag]
    offset: int
    limit: int
    count: int


class ListTagContentsResults(BaseModel):
    tag: Tag
    results: list[ListContentResult]
    offset: int
    limit: int
    count: int
