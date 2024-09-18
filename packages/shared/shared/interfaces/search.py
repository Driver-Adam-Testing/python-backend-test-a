from shared.interfaces.request import DriverRequest
from shared.interfaces.response import DriverResponse

# TODO: make result metadata a strict type.


class SearchInput(DriverRequest):
    query: str
    token_limit: int | None = None
    result_limit: int | None = 20
    algorithm: str = "semantic"
    content_type: str | list[str] | None = None
    workspace_id: str | None = None  # TODO: lock this down in auth
    codebase_id: str | None = None
    relative_path: str | list[str] | None = None
    organization_id: str | None = None


class SearchResult(DriverResponse):
    content: str
    score: float
    metadata: dict


class SearchResults(DriverResponse):
    results: list[SearchResult]
