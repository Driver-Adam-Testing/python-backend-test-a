import re

from database.models_v1 import Chunk, ContentMetadata
from rank_bm25 import BM25Okapi
from shared.embedding.text_embedder import TextEmbedder
from shared.interfaces.search import SearchInput, SearchResult, SearchResults
from sqlmodel import Session, asc, or_, select


def tokenize_for_bm25(text: str):
    return re.findall(r"\b[\w_]+(?:'[\w_]+)?\b", text.lower())


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
        if isinstance(input.relative_path, str):
            statement = statement.where(
                ContentMetadata.relative_path.like(f"{input.relative_path}%")
            )
        elif isinstance(input.relative_path, list):
            statement = statement.where(
                or_(
                    *[
                        ContentMetadata.relative_path.like(f"{file_path}%")
                        for file_path in input.relative_path
                    ]
                )
            )

    statement = statement.where(
        Chunk.text_embedding_3_small.l2_distance(embedded_query) <= 1.3
    )

    statement = statement.order_by(asc("score"))

    if input.result_limit:
        if input.algorithm != "semantic":
            statement = statement.limit(max(input.result_limit * 10, 500))
        else:
            statement = statement.limit(input.result_limit)

    results = session.exec(statement).all()
    search_results = []

    def process_result(
        c,
        cm,
        score,
        aggregate_score,
        accumulated_tokens,
        text_score=None,
        path_score=None,
    ):
        c: Chunk = c
        cm: ContentMetadata = cm
        if input.token_limit is not None:
            if accumulated_tokens > input.token_limit:
                return False, accumulated_tokens
        token_count = (
            c.token_count
            if c.token_count is not None
            else int(len(c.text.split()) / 2.5)
        )
        accumulated_tokens += token_count
        metadata = {
            "content_type": cm.content_type,
            "relative_path": cm.relative_path,
            "workspace_id": cm.workspace_id,
            "codebase_id": cm.codebase_id,
            "chunk_number": c.chunk_number,
            "line_number": c.line_number,
            "semantic_score": score,
        }
        if text_score is not None and path_score is not None:
            metadata.update(
                {"text_keyword_score": text_score, "path_keyword_score": path_score}
            )
        search_results.append(
            SearchResult(
                content=c.text,
                score=aggregate_score,
                metadata=metadata,
            )
        )
        return True, accumulated_tokens

    accumulated_tokens = 0

    if input.algorithm == "semantic":
        for c, cm, score in results:
            normalized_semantic_score = (2 - score) / 2  # Invert and normalize to 0-1
            success, accumulated_tokens = process_result(
                c, cm, score, normalized_semantic_score, accumulated_tokens
            )
            if not success:
                break
    else:
        texts = [c.text for c, cm, score in results]
        relative_paths = [cm.relative_path for c, cm, score in results]
        tokenized_query = tokenize_for_bm25(input.query)
        tokenized_texts = [tokenize_for_bm25(doc) for doc in texts]
        tokenized_paths = [tokenize_for_bm25(doc) for doc in relative_paths]
        bm25_text = BM25Okapi(tokenized_texts)
        bm25_relative_path = BM25Okapi(tokenized_paths)
        text_scores = bm25_text.get_scores(tokenized_query)
        path_scores = bm25_relative_path.get_scores(tokenized_query)

        for (c, cm, score), text_score, path_score in zip(
            results, text_scores, path_scores, strict=False
        ):
            normalized_semantic_score = (2 - score) / 2  # Invert and normalize to 0-1
            normalized_text_score = min(text_score, 7) / 7
            normalized_path_score = min(path_score, 7) / 7

            semantic_weight = 1
            text_weight = 0.5
            path_weight = 0.5

            aggregate_score = (
                normalized_semantic_score * semantic_weight
                + normalized_text_score * text_weight
                + normalized_path_score * path_weight
            ) / (semantic_weight + text_weight + path_weight)

            success, accumulated_tokens = process_result(
                c,
                cm,
                score,
                aggregate_score,
                accumulated_tokens,
                text_score,
                path_score,
            )
            if not success:
                break
    search_results.sort(key=lambda x: x.score, reverse=True)

    # Trim the search_results to only include up to input.result_limit
    search_results = search_results[: input.result_limit]

    # Add result_number to metadata
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)
