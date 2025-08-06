import logging
import re
from uuid import UUID

from database.db import get_session
from database.models_v1 import ChunkAndEmbedding, ContentKind, DerivedContent
from database.models_v2 import Node, PrimaryAsset, Version
from rank_bm25 import BM25Okapi
from sqlalchemy import Select
from sqlalchemy.orm import aliased, selectinload
from sqlmodel import Session, and_, asc, select, text

from shared.embedding.text_embedder import batch_embed_text
from shared.interfaces.search import (
    SearchAlgorithm,
    SearchInput,
    SearchResult,
    SearchResults,
)

# ---- Constants ----
SEMANTIC_WEIGHT = 1.0
BM25_WEIGHT = 1.0
MAX_BM25_SCORE = 6.0
SEMANTIC_SCORE_IGNORE_THRESHOLD = 1.25
CHARS_PER_TOKEN_APPROXIMATION = 2.5


# ---- Utility Functions ----
def tokenize_for_bm25(text: str) -> list[str]:
    """
    Tokenize a given text to prepare it for BM25 scoring.

    :param text: The input text.
    :return: A list of tokens.
    """
    return re.findall(r"\b[\w_]+(?:'[\w_]+)?\b", text.lower())


def get_bm25_scores(query: str, texts: list[str]) -> list[float]:
    """
    Compute BM25 scores for a set of texts against a given query.

    :param query: The search query string.
    :param texts: List of documents to score.
    :return: A list of BM25 scores, in the same order as texts.
    """
    tokenized_query = tokenize_for_bm25(query)
    tokenized_docs = [tokenize_for_bm25(doc) for doc in texts]
    bm25_model = BM25Okapi(tokenized_docs)
    return bm25_model.get_scores(tokenized_query)


def overall_score(
    semantic_score: float | None = None, bm25_score: float | None = None
) -> float:
    """
    Compute the overall score from semantic and BM25 scores.
    - Semantic score is normalized to [0,1], then cubed to emphasize distance from 1.0.
    - BM25 is a relative score, so we do a naive normalization.

    :param semantic_score: The semantic similarity score (distance-based).
    :param bm25_score: The BM25 score (higher = more relevant).
    :return: A single float representing the combined score, in range [0,1].
    """
    # Normalize semantic score to [0,1], then cube to exaggerate differences
    if semantic_score is not None:
        normalized_semantic = (1 - abs(1 - semantic_score)) ** 3
        normalized_semantic = max(0.0, normalized_semantic)
    else:
        normalized_semantic = None

    # Naive BM25 normalization
    if bm25_score is not None:
        normalized_bm25 = 1 - (1 / (1 + bm25_score))
        normalized_bm25 = max(0.0, normalized_bm25)
    else:
        normalized_bm25 = None

    # Combine the two
    if normalized_semantic is None:
        return normalized_bm25 if normalized_bm25 is not None else 0.0
    if normalized_bm25 is None:
        return normalized_semantic

    return (normalized_semantic * SEMANTIC_WEIGHT + normalized_bm25 * BM25_WEIGHT) / (
        SEMANTIC_WEIGHT + BM25_WEIGHT
    )


def create_filtered_chunk_statement(
    organization_id: str,
    node_ids: list[UUID] | None = None,
    content_kinds: list[ContentKind] | None = None,
    embedded_query: list | None = None,
) -> Select:
    """
    Create the base SQL statement for filtering relevant ChunkAndEmbedding records.

    :param organization_id: The organization in which we want to search.
    :param node_ids: Optional list of node UUIDs to further filter.
    :param embedded_query: If provided, includes the L2 distance from the query vector.
    :return: The SQLAlchemy Select statement.
    """
    NodeAlias = aliased(Node)

    # Start with a statement that selects (ChunkAndEmbedding, <semantic_score>).
    if embedded_query is not None:
        stmt = select(
            ChunkAndEmbedding,
            ChunkAndEmbedding.text_embedding_3_small.l2_distance(embedded_query).label(
                "semantic_score"
            ),
        )
    else:
        stmt = select(ChunkAndEmbedding, select(0).label("semantic_score"))

    stmt = (
        stmt.distinct()
        .options(
            selectinload(ChunkAndEmbedding.content)
            .selectinload(DerivedContent.node)
            .selectinload(Node.version)
        )
        .join(DerivedContent)
        .join(Node)
        .join(Version)
        .join(PrimaryAsset)
        .where(PrimaryAsset.organization_id == organization_id)
    )

    if content_kinds:
        stmt = stmt.where(DerivedContent.content_kind.in_(content_kinds))

    if node_ids:
        # Example usage: This allows searching within a node and all its sub-paths.
        stmt = stmt.join(
            NodeAlias,
            and_(
                NodeAlias.version_id == Node.version_id,
                Node.relative_path.like(NodeAlias.relative_path + "%"),
            ),
        ).where(NodeAlias.id.in_(node_ids))

    return stmt


# ---- Public Search Functions ----
def search_content_without_session(input: SearchInput) -> SearchResults:
    """
    Convenience function that manages its own Session, then calls search_content.

    :param input: The user-provided search input config.
    :return: The search results as a SearchResults object.
    """
    with get_session() as session:
        return search_content(session, input)


def search_content(session: Session, input: SearchInput) -> SearchResults:
    """
    Route the search to the correct algorithm: KEYWORD, SEMANTIC, or HYBRID.

    :param session: The active SQLModel session.
    :param input: The user-provided search input config.
    :return: The search results as a SearchResults object.
    """
    if input.algorithm == SearchAlgorithm.KEYWORD:
        return keyword_search(session, input)
    elif input.algorithm == SearchAlgorithm.SEMANTIC:
        return semantic_search(session, input)
    elif input.algorithm == SearchAlgorithm.HYBRID:
        return hybrid_search(session, input)
    else:
        raise ValueError(f"Unsupported algorithm: {input.algorithm}")


def semantic_search(session: Session, input: SearchInput) -> SearchResults:
    """
    Perform purely semantic (vector-based) search.

    :param session: The active SQLModel session.
    :param input: The user-provided search input.
    :return: The search results as a SearchResults object.
    """
    logger = logging.getLogger(__name__)

    # Embed the query text
    embedded_query = batch_embed_text([input.query])[0]

    # Create filtered statement that includes semantic scores
    stmt = create_filtered_chunk_statement(
        organization_id=input.organization_id,
        node_ids=input.node_ids,
        embedded_query=embedded_query,
        content_kinds=input.content_kinds,
    ).order_by(asc("semantic_score"))

    if input.limit:
        stmt = stmt.limit(input.limit)
    session.exec(text("SET hnsw.ef_search=400;"))
    results = session.exec(stmt).all()
    logger.debug("Raw semantic search results: %s", results)

    if not results:
        return SearchResults(results=[])

    # Convert DB results to SearchResults
    search_results = []
    for chunk, score in results:
        metadata = {
            "chunk_number": chunk.chunk_number,
        }
        version_display_name = (
            chunk.content.node.version.vcs_hash
            if chunk.content.node.version.vcs_hash
            else "Unversioned"
        )
        search_results.append(
            SearchResult(
                content=chunk.text,
                score=overall_score(semantic_score=score),
                metadata=metadata,
                relative_path=chunk.content.node.relative_path,
                version_display_name=version_display_name,
                version_id=chunk.content.node.version_id,
                node_id=chunk.content.node_id,
            )
        )

    # Sort by score descending
    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.limit]

    # Label results
    for idx, result in enumerate(search_results, start=1):
        result.metadata["result_number"] = idx

    return SearchResults(results=search_results)


def keyword_search(session: Session, input: SearchInput) -> SearchResults:
    """
    Perform purely keyword-based search (TS vector).

    :param session: The active SQLModel session.
    :param input: The user-provided search input.
    :return: The search results as a SearchResults object.
    """
    # Create statement without semantic score
    stmt = create_filtered_chunk_statement(
        organization_id=input.organization_id,
        node_ids=input.node_ids,
        content_kinds=input.content_kinds,
    ).where(ChunkAndEmbedding.__ts_vector__.match(input.query))
    session.exec(text("SET hnsw.ef_search=400;"))
    db_results = session.exec(stmt).all()
    if not db_results:
        return SearchResults(results=[])

    # Prepare texts for BM25
    texts_for_bm25 = [f"{c.text} {c.content.node.relative_path}" for c, _ in db_results]
    bm25_scores = get_bm25_scores(input.query, texts_for_bm25)

    # Convert DB results to SearchResults
    search_results = []
    for (chunk, _), bm25_score in zip(db_results, bm25_scores):
        metadata = {
            "version_id": chunk.content.node.version_id,
            "chunk_number": chunk.chunk_number,
        }
        version_display_name = (
            chunk.content.node.version.vcs_hash
            if chunk.content.node.version.vcs_hash
            else "Unversioned"
        )
        search_results.append(
            SearchResult(
                content=chunk.text,
                score=overall_score(bm25_score=bm25_score),
                metadata=metadata,
                relative_path=chunk.content.node.relative_path,
                version_display_name=version_display_name,
                version_id=chunk.content.node.version_id,
                node_id=chunk.content.node_id,
            )
        )

    # Sort by score descending
    search_results.sort(key=lambda x: x.score, reverse=True)

    # Apply final limit
    search_results = search_results[: input.limit]

    # Label results
    for idx, result in enumerate(search_results, start=1):
        result.metadata["result_number"] = idx

    return SearchResults(results=search_results)


def hybrid_search(session: Session, input: SearchInput) -> SearchResults:
    """
    Hybrid search combines semantic (vector) search and keyword (TS vector/BM25) search.

    Steps:
      1. Run semantic search (embedding) up to 2x limit.
      2. Run lexical (TS vector) search up to 2x limit.
      3. Combine and deduplicate results, preserving semantic scores where available.
      4. Compute BM25 across combined results.
      5. Compute overall scores, sort, and return final results.

    :param session: The active SQLModel session.
    :param input: The user-provided search input.
    :return: The search results as a SearchResults object.
    """
    # 1. Run semantic search
    embedded_query = batch_embed_text([input.query])[0]
    stmt_semantic = (
        create_filtered_chunk_statement(
            organization_id=input.organization_id,
            node_ids=input.node_ids,
            embedded_query=embedded_query,
            content_kinds=input.content_kinds,
        )
        .order_by(asc("semantic_score"))
        .limit(2 * input.limit)
    )
    results_semantic = session.exec(stmt_semantic).all()

    # 2. Run lexical search (TS vector)
    stmt_lexical = (
        create_filtered_chunk_statement(
            organization_id=input.organization_id, node_ids=input.node_ids
        )
        .where(ChunkAndEmbedding.__ts_vector__.match(input.query))
        .limit(2 * input.limit)
    )
    session.exec(text("SET hnsw.ef_search=400;"))
    results_lexical = session.exec(stmt_lexical).all()

    # 3. Combine / deduplicate
    # Key by chunk.id -> (chunk, semantic_score)
    chunk_map: dict[str, (ChunkAndEmbedding, float | None)] = {}
    # Fill from semantic search
    for chunk, sem_score in results_semantic:
        chunk_map[chunk.id] = (chunk, sem_score)
    # Fill from lexical search
    for chunk, _ in results_lexical:
        if chunk.id not in chunk_map:
            chunk_map[chunk.id] = (chunk, None)

    combined_chunks = list(chunk_map.values())

    if not combined_chunks:
        return SearchResults(results=[])

    # 4. Compute BM25 on combined results
    texts_for_bm25 = [
        f"{chunk.text} {chunk.content.node.relative_path}"
        for chunk, _ in combined_chunks
    ]
    bm25_scores = get_bm25_scores(input.query, texts_for_bm25)

    # 5. Compute overall score and assemble SearchResults
    search_results = []
    accumulated_tokens = 0

    for i, (chunk, sem_score) in enumerate(combined_chunks):
        # Respect token limit if provided
        if input.token_limit is not None and accumulated_tokens >= input.token_limit:
            break

        token_count = int(len(chunk.text.split()) / CHARS_PER_TOKEN_APPROXIMATION)
        accumulated_tokens += token_count

        metadata = {
            "chunk_number": chunk.chunk_number,
        }

        # Combine semantic and BM25
        hybrid_score = overall_score(
            semantic_score=sem_score, bm25_score=bm25_scores[i]
        )
        version_display_name = (
            chunk.content.node.version.vcs_hash
            if chunk.content.node.version.vcs_hash
            else "Unversioned"
        )
        search_results.append(
            SearchResult(
                content=chunk.text,
                score=hybrid_score,
                relative_path=chunk.content.node.relative_path,
                version_display_name=version_display_name,
                version_id=chunk.content.node.version_id,
                node_id=chunk.content.node_id,
                metadata=metadata,
            )
        )

    # Sort final results by score descending, then limit
    search_results.sort(key=lambda x: x.score, reverse=True)
    search_results = search_results[: input.limit]

    # Label results
    for idx, result in enumerate(search_results, start=1):
        result.metadata["result_number"] = idx

    return SearchResults(results=search_results)
