
from pydantic import BaseModel

from app.schemas.content_schema import ListContentResult
from database.models_v1 import Tag


class ListTagsInput(BaseModel):
    name: str | None
    limit: int
    offset: int


class NewTagInput(BaseModel):
    name: str
    hexColor: str


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
