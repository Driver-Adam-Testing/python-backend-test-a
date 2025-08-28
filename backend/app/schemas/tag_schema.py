from typing import Literal

from app.schemas.content_schema import ListContentResult
from database.models_v2 import Tag
from pydantic import BaseModel, field_validator

TagType = Literal["tag", "collection"]


class ListTagsInput(BaseModel):
    name: str | None
    type: TagType | None
    limit: int
    offset: int


class TagInputBase(BaseModel):
    name: str
    hex_color: str

    @field_validator("name", "hex_color")
    @classmethod
    def strip_whitespace(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("hex_color")
    @classmethod
    def validate_hex_color(cls, value):
        # Check if the string matches the hex color format
        if (
            not value.startswith("#")
            or len(value) != 7
            or not all(c in "0123456789ABCDEFabcdef" for c in value[1:])
        ):
            raise ValueError("Invalid hex color format")
        return value


class NewTagInput(TagInputBase):
    type: TagType


class EditTagInput(TagInputBase):
    name: str | None = None
    hex_color: str | None = None


class CollectionSourceInput(BaseModel):
    include: bool


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
