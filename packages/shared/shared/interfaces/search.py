from enum import Enum
from uuid import UUID

from database.models_v2_enums import ContentKind

from shared.interfaces.request import DriverRequest
from shared.interfaces.response import DriverResponse


class SearchAlgorithm(str, Enum):
    KEYWORD = "KEYWORD"
    SEMANTIC = "SEMANTIC"
    HYBRID = "HYBRID"


class SearchInput(DriverRequest):
    limit: int | None = 20
    query: str
    algorithm: SearchAlgorithm = SearchAlgorithm.HYBRID
    token_limit: int | None = None
    content_kinds: list[ContentKind] | None = None
    node_ids: list[UUID] | None = None
    organization_id: str | None = None


class SearchResult(DriverResponse):
    content: str
    score: float
    metadata: dict


class SearchResults(DriverResponse):
    results: list[SearchResult]
