from uuid import UUID

from pydantic import BaseModel


class Reference(BaseModel):
    content: str
    score: float | None = None
    relative_path: str | None = None
    version_display_name: str | None = None
    version_id: UUID | None = None
    node_id: UUID | None = None
    chunk_id: UUID | None = None
    chunk_number: int | None = None
    metadata: dict | None = None
    tool_call_id: str | None = None

    def __hash__(self) -> int:
        return hash(self.content + str(self.node_id) + str(self.version_id))

    def __eq__(self, other: "Reference") -> bool:
        return hash(self) == hash(other)


class ReferenceSet(BaseModel):
    references: set[Reference] = set()

    def add_reference(self, reference: Reference) -> None:
        self.references.add(reference)
