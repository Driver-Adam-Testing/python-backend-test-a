import re

from database.models_v1 import (
    ChunkAndEmbedding,
    DerivedContent,
    DerivedContentType,
    Workspace,
)
from rank_bm25 import BM25Okapi
from sqlmodel import Session, asc, or_, select

from shared.embedding.text_embedder import batch_embed_text
from shared.interfaces.search import SearchInput, SearchResult, SearchResults


def tokenize_for_bm25(text: str):
    return re.findall(r"\b[\w_]+(?:'[\w_]+)?\b", text.lower())


def build_base_statement(input: SearchInput, embedded_query):
    statement = (
        select(
            ChunkAndEmbedding,
            DerivedContent,
            ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query).label(
                "score"
            ),
        )
        .join(Workspace)
        .join(DerivedContentType)
        .where(DerivedContent.id == ChunkAndEmbedding.content_id)
        .where(DerivedContent.workspace_id == Workspace.id)
        .where(DerivedContentType.id == DerivedContent.content_type_id)
    )

    if input.workspace_id:
        statement = statement.where(DerivedContent.workspace_id == input.workspace_id)

    if input.codebase_id:
        statement = statement.where(DerivedContent.codebase_id == input.codebase_id)

    if input.organization_id:
        statement = statement.where(Workspace.organization_id == input.organization_id)

    if input.content_type:
        if isinstance(input.content_type, str):
            statement = statement.where(
                DerivedContentType.type_name == input.content_type
            )
        elif isinstance(input.content_type, list):
            statement = statement.where(
                DerivedContentType.type_name.in_(input.content_type)
            )

    if input.relative_path:
        paths = []
        if isinstance(input.relative_path, str):
            paths = [input.relative_path]

        elif isinstance(input.relative_path, list):
            paths = input.relative_path

        statement = statement.where(
            or_(
                *[
                    or_(
                        DerivedContent.relative_path == file_path,
                        DerivedContent.relative_path.like(f"{file_path.rstrip('/')}/%"),
                    )
                    for file_path in paths
                ]
            )
        )

    return statement


def process_result(
    c: ChunkAndEmbedding,
    dc: DerivedContent,
    score: float,
    aggregate_score: float,
    accumulated_tokens: int,
    input: SearchInput,
    search_results: list,
    text_score: float = None,
    path_score: float = None,
):
    if input.token_limit is not None:
        if accumulated_tokens > input.token_limit:
            return False, accumulated_tokens
    token_count = int(len(c.text.split()) / 2.5)
    accumulated_tokens += token_count
    metadata = {
        "content_type": dc.content_type.type_name,
        "relative_path": dc.relative_path,
        "workspace_id": dc.workspace_id,
        "codebase_id": dc.codebase_id,
        "content_id": dc.id,
        "chunk_number": c.chunk_number,
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


def search_content(session: Session, input: SearchInput):
    if input.algorithm == "keyword":
        return keyword_search(session, input)
    elif input.algorithm == "semantic":
        return semantic_search(session, input)
    else:
        return hybrid_search(session, input)


def keyword_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement = build_base_statement(input, embedded_query)
    statement = statement.where(ChunkAndEmbedding.__ts_vector__.match(input.query))

    if input.result_limit:
        statement = statement.limit(input.result_limit)

    results = [
        SearchResult(
            content=c.text,
            score=s,
            metadata={
                "id": c.id,
                "workspace_id": cm.workspace_id,
                "codebase_id": cm.codebase_id,
                "content_type": cm.content_type,
                "relative_path": cm.relative_path,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            },
        )
        for c, cm, s in session.exec(statement).all()
    ]

    return SearchResults(results=results)


def semantic_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement = build_base_statement(input, embedded_query)
    statement = statement.where(
        ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query) <= 1.25
    )
    statement = statement.order_by(asc("score"))

    if input.result_limit:
        statement = statement.limit(input.result_limit)

    results = session.exec(statement).all()

    if not results:
        return SearchResults(results=[])

    search_results = []
    accumulated_tokens = 0

    for c, cm, score in results:
        normalized_semantic_score = (2 - score) / 2  # Invert and normalize to 0-1
        success, accumulated_tokens = process_result(
            c,
            cm,
            score,
            normalized_semantic_score,
            accumulated_tokens,
            input,
            search_results,
        )
        if not success:
            break

    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.result_limit]
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)


def hybrid_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement = build_base_statement(input, embedded_query)
    statement = statement.where(
        ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query) <= 1.25
    )
    statement = statement.order_by(asc("score"))

    if input.result_limit:
        statement = statement.limit(max(input.result_limit * 10, 500))

    results = session.exec(statement).all()

    if not results:
        return SearchResults(results=[])

    search_results = []
    accumulated_tokens = 0

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
        normalized_semantic_score = (
            2 - score
        ) / 2  # Invert and normalize to 0-1 TODO: make this distance from 1
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
            input,
            search_results,
            text_score,
            path_score,
        )
        if not success:
            break

    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.result_limit]
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)
