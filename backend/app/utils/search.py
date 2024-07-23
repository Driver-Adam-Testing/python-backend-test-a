from database.models_v1 import Chunk, ContentMetadata, Workspace
from pydantic import BaseModel
from sqlmodel import Session, asc, or_, select

from app.utils.content_scope import build_content_scope
from app.utils.text_embedder import TextEmbedder


class SearchInput(BaseModel):
    query: str
    token_limit: int | None = None
    result_limit: int | None = 20
    algorithm: str = "semantic"
    content_type: str | list[str] | None = None
    workspace_id: str | None = None
    codebase_id: str | None = None
    relative_path: str | None = None


class SearchResult(BaseModel):
    content: str
    score: float
    experimental_content_scope: str  # Format: organization_id:workspace_id:codebase_id:relative_path
    metadata: dict


class SearchResults(BaseModel):
    results: list[SearchResult]


def search_content_metadata(
    session: Session, organization_id: str | None, input: SearchInput
):
    embedded_query = TextEmbedder().batch_embed_text([input.query])[0]

    statement = (
        select(
            Chunk,
            ContentMetadata,
            Chunk.text_embedding_3_small.l2_distance(embedded_query).label("score"),
            Workspace,
        )
        .where(ContentMetadata.id == Chunk.content_metadata_id)
        .where(ContentMetadata.workspace_id == Workspace.id)
    )

    if organization_id:
        statement = statement.where(Workspace.organization_id == organization_id)

    if input.workspace_id:
        statement = statement.where(ContentMetadata.workspace_id == input.workspace_id)

    if input.codebase_id:
        statement = statement.where(ContentMetadata.codebase_id == input.codebase_id)

    if input.content_type:
        if isinstance(input.content_type, str):
            statement = statement.where(
                ContentMetadata.content_type == input.content_type
            )
        elif isinstance(input.content_type, list):
            statement = statement.where(
                ContentMetadata.content_type.in_(input.content_type)
            )

    if input.relative_path:
        statement = statement.where(
            or_(
                *[
                    ContentMetadata.relative_path.like(f"{file_path}%")
                    for file_path in input.relative_path
                ]
            )
        )

    statement = statement.order_by(asc("score"))

    if input.result_limit:
        statement = statement.limit(input.result_limit)

    results = session.exec(statement).all()
    search_results = []

    accumulated_tokens = 0
    for c, cm, score, _ in results:
        c: Chunk = c
        cm: ContentMetadata = cm
        if input.token_limit is not None:
            if accumulated_tokens > input.token_limit:
                break
        token_count = (
            c.token_count
            if c.token_count is not None
            else int(len(c.text.split()) / 2.5)
        )
        accumulated_tokens += token_count
        search_results.append(
            SearchResult(
                content=c.text,
                score=score,
                experimental_content_scope=build_content_scope(
                    organization_id=organization_id,
                    workspace_id=cm.workspace_id,
                    codebase_id=cm.codebase_id,
                    relative_path=cm.relative_path,
                ),
                metadata={
                    "content_type": cm.content_type,
                    "relative_path": cm.relative_path,
                    "workspace_id": cm.workspace_id,
                    "codebase_id": cm.codebase_id,
                    "chunk_number": c.chunk_number,
                    "line_number": c.line_number,
                },
            )
        )
    return SearchResults(results=search_results)
