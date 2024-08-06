from database.models_v1 import Chunk, ContentMetadata
from shared.embedding.text_embedder import TextEmbedder
from shared.interfaces.search import SearchInput, SearchResult, SearchResults
from sqlmodel import Session, asc, or_, select


def search_content_metadata(
    session: Session, organization_id: str | None, input: SearchInput
):
    embedded_query = TextEmbedder().batch_embed_text([input.query])[0]

    statement = select(
        Chunk,
        ContentMetadata,
        Chunk.text_embedding_3_small.l2_distance(embedded_query).label("score"),
    ).where(ContentMetadata.id == Chunk.content_metadata_id)

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
    print(statement)
    import time

    start_time = time.time()
    results = session.exec(statement).all()
    end_time = time.time()

    elapsed_time_ms = (end_time - start_time) * 1000
    print(f"Query execution time: {elapsed_time_ms:.2f} ms")
    search_results = []

    accumulated_tokens = 0
    for c, cm, score in results:
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
