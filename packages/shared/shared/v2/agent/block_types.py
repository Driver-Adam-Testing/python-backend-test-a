from pydantic import BaseModel


class ContentBlock(BaseModel):
    content: str
    rationale: str


class ParagraphBlock(BaseModel):
    paragraph_content: str
    rationale: str


class ListBlock(BaseModel):
    list_content: list[str]
    rationale: str


class DiagramBlock(BaseModel):
    diagram_content: str
    rationale: str


class TableBlock(BaseModel):
    row_contents: list[list[str]]
    has_header: bool
    rationale: str


class CodeBlock(BaseModel):
    code_content: str
