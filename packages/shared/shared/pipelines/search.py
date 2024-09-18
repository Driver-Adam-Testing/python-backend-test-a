import math
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
    statement = statement.order_by(asc("score"))
    return statement


def calculate_aggregate_score(semantic_score: float, bm25_score: float = None):
    # Normalize the semantic score to be between 0 and 1
    normalized_semantic_score = max(0, 1 - math.sqrt(abs(semantic_score - 1)))
    semantic_weight = 1
    bm25_weight = 1

    if bm25_score is not None:
        # Normalize the BM25 score to be between 0 and 1
        normalized_bm25_score = min(bm25_score, MAX_BM25_SCORE) / MAX_BM25_SCORE
        # Calculate the weighted aggregate score between 0 and 1
        aggregate_score = (
            normalized_semantic_score * semantic_weight
            + normalized_bm25_score * bm25_weight
        ) / (semantic_weight + bm25_weight)
    else:
        # If no BM25 score, the aggregate score is just the normalized semantic score
        aggregate_score = normalized_semantic_score

    return aggregate_score


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

    results = sorted(
        [
            SearchResult(
                content=c.text,
                score=BM25Okapi([c.text + " " + cm.relative_path]).get_scores(
                    input.query
                )[0],
                metadata={
                    "id": c.id,
                    "workspace_id": cm.workspace_id,
                    "codebase_id": cm.codebase_id,
                    "content_type": cm.content_type.type_name,
                    "relative_path": cm.relative_path,
                    "semantic_score": s,
                    "keyword_score": BM25Okapi(
                        [c.text + " " + cm.relative_path]
                    ).get_scores(input.query)[0],
                },
            )
            for c, cm, s in session.exec(statement).all()
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
        aggregate_score = calculate_aggregate_score(score)
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
                score=aggregate_score,
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

    tokenized_query = tokenize_for_bm25(input.query)
    tokenized_texts = [
        tokenize_for_bm25(c.text + " " + cm.relative_path) for c, cm, s in results
    ]

    bm25_text = BM25Okapi(tokenized_texts)
    text_scores = bm25_text.get_scores(tokenized_query)

    for idx, (c, cm, score) in enumerate(results):
        if input.token_limit is not None and accumulated_tokens > input.token_limit:
            break
        token_count = int(len(c.text.split()) / 2.5)
        accumulated_tokens += token_count
        bm25_score = text_scores[idx]
        aggregate_score = calculate_aggregate_score(score, bm25_score)
        metadata = {
            "content_type": cm.content_type.type_name,
            "relative_path": cm.relative_path,
            "workspace_id": cm.workspace_id,
            "codebase_id": cm.codebase_id,
            "content_id": cm.id,
            "chunk_number": c.chunk_number,
            "semantic_score": score,
            "bm25_score": text_scores[idx],
        }
        search_results.append(
            SearchResult(
                content=c.text,
                score=aggregate_score,
                metadata=metadata,
            )
        )

    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.result_limit]
    for idx, result in enumerate(search_results):
        result.metadata["result_number"] = idx + 1

    return SearchResults(results=search_results)
