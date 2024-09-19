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

SEMANTIC_WEIGHT = 1.0
BM25_WEIGHT = 1.0
MAX_BM25_SCORE = 6.0
SEMANTIC_SCORE_IGNORE_THRESHOLD = 1.25
CHARS_PER_TOKEN_APPROXIMATION = 2.5


def get_bm25_scores(query: str, texts: list[str]):
    def tokenize_for_bm25(text: str):
        return re.findall(r"\b[\w_]+(?:'[\w_]+)?\b", text.lower())

    tokenized_query = tokenize_for_bm25(query)
    tokenized_text = [tokenize_for_bm25(text) for text in texts]
    bm25_text = BM25Okapi(tokenized_text)
    text_scores = bm25_text.get_scores(tokenized_query)

    return text_scores


def overall_score(semantic_score: float | None = None, bm25_score: float | None = None):
    # Normalize the semantic score to be between 0 and 1, cube it to exaggerate distance from 1.0
    normalized_semantic_score = (
        max(0, (1 - abs(1 - semantic_score)) ** 3)
        if semantic_score is not None
        else None
    )
    # TODO: BM25 is a relative score, so you can't score just one record. Figure out how to normalize this effectively
    normalized_bm25_score = (
        max(0, 1 - (1 / (1 + bm25_score))) if bm25_score is not None else None
    )

    if normalized_semantic_score is None:
        return normalized_bm25_score
    if normalized_bm25_score is None:
        return normalized_semantic_score

    # Calculate the weighted aggregate score between 0 and 1
    aggregate_score = (
        normalized_semantic_score * SEMANTIC_WEIGHT
        + normalized_bm25_score * BM25_WEIGHT
    ) / (SEMANTIC_WEIGHT + BM25_WEIGHT)

    return aggregate_score


def build_base_statement(input: SearchInput, embedded_query: any) -> any:
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
        .where(DerivedContentType.id == DerivedContent.content_type_id)
    )
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

    if input.paths:
        if isinstance(input.paths, str):
            input.paths = [input.paths]
        statement = statement.where(
            or_(
                *[
                    or_(
                        DerivedContent.relative_path == file_path,
                        DerivedContent.relative_path.like(f"{file_path.rstrip('/')}/%"),
                    )
                    for file_path in input.paths
                ]
            )
        )

    statement = statement.order_by(asc("score"))
    return statement


def search_content(session: Session, input: SearchInput):
    if input.algorithm == "keyword":
        return keyword_search(session, input)
    elif input.algorithm == "semantic":
        return semantic_search(session, input)
    elif input.algorithm == "hybrid":
        return hybrid_search(session, input)
    else:
        raise ValueError(f"Unsupported algorithm: {input.algorithm}")


def keyword_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement = build_base_statement(input, embedded_query)
    statement = statement.where(ChunkAndEmbedding.__ts_vector__.match(input.query))

    if input.result_limit:
        statement = statement.limit(input.result_limit)

    db_results = session.exec(statement).all()
    keyword_scores = get_bm25_scores(
        input.query, [c.text + " " + cm.relative_path for c, cm, _ in db_results]
    )
    results = sorted(
        [
            SearchResult(
                content=c.text,
                score=overall_score(bm25_score=bm25_score),
                metadata={
                    "id": c.id,
                    "workspace_id": cm.workspace_id,
                    "codebase_id": cm.codebase_id,
                    "content_type": cm.content_type.type_name,
                    "relative_path": cm.relative_path,
                    "semantic_score": s,
                    "keyword_score": bm25_score,
                },
            )
            for (c, cm, s), bm25_score in zip(db_results, keyword_scores)
        ],
        key=lambda result: result.score,
        reverse=True,
    )

    return SearchResults(results=results)


def semantic_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement = build_base_statement(input, embedded_query)
    statement = statement.where(
        ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query)
        <= SEMANTIC_SCORE_IGNORE_THRESHOLD
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
        if input.token_limit is not None and accumulated_tokens > input.token_limit:
            break
        token_count = int(len(c.text.split()) / CHARS_PER_TOKEN_APPROXIMATION)
        accumulated_tokens += token_count
        metadata = {
            "content_type": cm.content_type.type_name,
            "relative_path": cm.relative_path,
            "workspace_id": cm.workspace_id,
            "codebase_id": cm.codebase_id,
            "content_id": cm.id,
            "chunk_number": c.chunk_number,
            "semantic_score": score,
        }
        search_results.append(
            SearchResult(
                content=c.text,
                score=overall_score(score),
                metadata=metadata,
            )
        )

    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.result_limit]
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)


def hybrid_search(session: Session, input: SearchInput):
    embedded_query = batch_embed_text([input.query])[0]
    statement_l2 = build_base_statement(input, embedded_query)
    statement_l2 = statement_l2.where(
        ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query) <= 1.25
    ).order_by(asc("score"))

    statement_tsvector = build_base_statement(input, embedded_query)
    statement_tsvector = statement_tsvector.where(
        ChunkAndEmbedding.__ts_vector__.match(input.query)
    ).order_by(asc("score"))

    if input.result_limit:
        statement_l2 = statement_l2.limit(input.result_limit)
        statement_tsvector = statement_tsvector.limit(input.result_limit)

    results_l2 = session.exec(statement_l2).all()
    results_tsvector = session.exec(statement_tsvector).all()

    results = list(
        {(c.id, cm.id, score) for c, cm, score in results_l2 + results_tsvector}
    )
    results = [
        (
            next(
                c
                for c in results_l2 + results_tsvector
                if c[0].id == c_id and c[1].id == cm_id
            )
        )
        for c_id, cm_id, score in results
    ]

    if not results:
        return SearchResults(results=[])

    search_results = []
    accumulated_tokens = 0

    keyword_scores = get_bm25_scores(
        input.query, [c.text + " " + cm.relative_path for c, cm, _ in results]
    )
    for idx, (c, cm, score) in enumerate(results):
        if input.token_limit is not None and accumulated_tokens > input.token_limit:
            break
        token_count = int(len(c.text.split()) / 2.5)
        accumulated_tokens += token_count
        metadata = {
            "content_type": cm.content_type.type_name,
            "relative_path": cm.relative_path,
            "workspace_id": cm.workspace_id,
            "codebase_id": cm.codebase_id,
            "content_id": cm.id,
            "chunk_number": c.chunk_number,
            "semantic_score": score,
            "bm25_score": keyword_scores[idx],
        }
        search_results.append(
            SearchResult(
                content=c.text,
                score=overall_score(
                    semantic_score=score, bm25_score=keyword_scores[idx]
                ),
                metadata=metadata,
            )
        )

    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.result_limit]
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)
