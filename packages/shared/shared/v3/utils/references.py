from collections.abc import Iterable, Iterator
from uuid import UUID

from pydantic import BaseModel


# TODO: make content chunks? so that we have sections of a document that fill in the context of the reference?
class Reference(BaseModel):
    """
    A reference to a node in the graph.
    """

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

    @property
    def short_path(self) -> str:
        parts = self.relative_path.split("/")
        if len(parts) > 3:
            return f"{parts[0]}/.../{parts[-2]}/{parts[-1]}"
        return self.relative_path


class ReferenceSet(BaseModel, Iterable):
    """
    A set of references.

    This class is a wrapper around a set of references. It implements the Iterable interface, so it can be used in for loops.
    """

    references: set[Reference] = set()

    @classmethod
    def from_list_of_reference_sets(
        cls, reference_sets: list["ReferenceSet"]
    ) -> "ReferenceSet":
        return cls(references=set().union(*[r.references for r in reference_sets]))

    def add_reference(self, reference: Reference) -> None:
        self.references.add(reference)

    def __iter__(self) -> Iterator[Reference]:
        return iter(sorted(self.references, key=lambda r: r.score or 0, reverse=True))

    def __len__(self) -> int:
        return len(self.references)
