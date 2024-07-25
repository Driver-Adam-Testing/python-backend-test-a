from database.models_v1 import DerivedContent
from pydantic import BaseModel
from sqlmodel import Session

from app.api.auth import CurrentUser


class ListContentInput(BaseModel):
    text: str | None
    limit: int | None = 20
    offset: int | None = 0
    sort: str | None = None
    # sortDirection: "ASC" | "DESC" | None = None
    # date: TODO - format? single date? date ranges? > date?
    content_type: list[
        str
    ] | None = None  # TODO - how do we get these strings to the UI? Do we need a list of derived content types?
    labels: list[str] | None = None


class ListContentResults(BaseModel):
    results: list[
        DerivedContent
    ]  # TODO - separate models from DB? This is where Andrew is migrating content to
    offset: int
    limit: int


def list_content(session: Session, user: CurrentUser, input: ListContentInput):
    return ListContentResults(result=[], offset=1, limit=2)
    # embedded_query = TextEmbedder().batch_embed_text([input.query])[0]

    # statement = select(
    #     Chunk,
    #     ContentMetadata,
    #     Chunk.text_embedding_3_small.l2_distance(embedded_query).label("score"),
    # ).where(ContentMetadata.id == Chunk.content_metadata_id)

    # if input.workspace_id:
    #     statement = statement.where(ContentMetadata.workspace_id == input.workspace_id)

    # if input.codebase_id:
    #     statement = statement.where(ContentMetadata.codebase_id == input.codebase_id)

    # if input.content_type:
    #     if isinstance(input.content_type, str):
    #         statement = statement.where(
    #             ContentMetadata.content_type == input.content_type
    #         )
    #     elif isinstance(input.content_type, list):
    #         statement = statement.where(
    #             ContentMetadata.content_type.in_(input.content_type)
    #         )

    # if input.relative_path:
    #     statement = statement.where(
    #         or_(
    #             *[
    #                 ContentMetadata.relative_path.like(f"{file_path}%")
    #                 for file_path in input.relative_path
    #             ]
    #         )
    #     )

    # statement = statement.order_by(asc("score"))

    # if input.result_limit:
    #     statement = statement.limit(input.result_limit)

    # results = session.exec(statement).all()
    # search_results = []

    # accumulated_tokens = 0
    # for c, cm, score in results:
    #     c: Chunk = c
    #     cm: ContentMetadata = cm
    #     if input.token_limit is not None:
    #         if accumulated_tokens > input.token_limit:
    #             break
    #     token_count = (
    #         c.token_count
    #         if c.token_count is not None
    #         else int(len(c.text.split()) / 2.5)
    #     )
    #     accumulated_tokens += token_count
    #     search_results.append(
    #         SearchResult(
    #             content=c.text,
    #             score=score,
    #             metadata={
    #                 "content_type": cm.content_type,
    #                 "relative_path": cm.relative_path,
    #                 "workspace_id": cm.workspace_id,
    #                 "codebase_id": cm.codebase_id,
    #                 "chunk_number": c.chunk_number,
    #                 "line_number": c.line_number,
    #             },
    #         )
    #     )
    # return SearchResults(results=search_results)
