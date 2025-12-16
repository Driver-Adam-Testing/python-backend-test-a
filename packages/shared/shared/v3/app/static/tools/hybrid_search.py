from database.db import get_session
from database.models import ChunkAndEmbedding, DerivedContent
from shared.embedding.text_embedder import batch_embed_text
from shared.pipelines.search import (
    get_bm25_scores,
    overall_score,
)
from shared.v3.globals.glossary import (
    REFERENCE,
    REFERENCE_CONTENT,
    REFERENCE_LIST,
    REFERENCE_RELATIVE_PATH,
    SEARCH_QUERY,
    TOOL_ERROR_MESSAGE,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import (
    LlmTool,
)
from shared.v3.utils.references import Reference
from sqlalchemy.orm import selectinload
from sqlmodel import select, text


class HybridSearchTool(LlmTool):
    """
    HybridSearchTool performs a hybrid search combining keyword and semantic search
    within a content repository of code and technical documentation.

    You can use this tool to search the codebase and files to obtain context for your response.
    Consider using keywords and descriptions of the documentation information or source code snippets you're looking for.
    ALWAYS include the name of the top level directory(ies) in the query string, unless searching for a specific symbol or function name.
    Attributes:
        search_query (str): The query string.
    """

    search_query: str

    def _execute(self) -> None:
        embedded_query: list[float] = batch_embed_text([self.search_query])[0]

        with get_session() as session:
            session.exec(text("SET hnsw.ef_search=400;"))
            stmt = (
                select(
                    ChunkAndEmbedding,
                    ChunkAndEmbedding.text_embedding_3_small.l2_distance(
                        embedded_query
                    ).label("semantic_score"),
                    DerivedContent.node_id.label("node_id"),
                )
                .join(DerivedContent, ChunkAndEmbedding.content_id == DerivedContent.id)
                .options(selectinload(ChunkAndEmbedding.content))
                .where(
                    DerivedContent.node_id.in_(
                        [
                            version_node.node_id
                            for version_node in self.datasource.version_nodes
                        ]
                    )
                )
                .order_by("semantic_score")
                .limit(40)
            )

            results = session.exec(stmt).all()

            if not results:
                return

            chunks, semantic_scores, node_ids = zip(*results)

            # Compute BM25 scores
            texts_for_bm25 = [chunk.text for chunk in chunks]
            bm25_scores = get_bm25_scores(self.search_query, texts_for_bm25)

            # Combine scores
            combined_results = []
            for chunk, bm25_score, sem_score, node_id in zip(
                chunks, bm25_scores, semantic_scores, node_ids
            ):
                combo_score = overall_score(
                    semantic_score=sem_score, bm25_score=bm25_score
                )
                combined_results.append((chunk, combo_score, node_id))

            # Sort by combined score descending
            sorted_results = sorted(combined_results, key=lambda x: x[1], reverse=True)

            # Limit to top 15
            top_results = sorted_results[:15]

            for chunk, combo_score, node_id in top_results:
                # Safely extract metadata from chunk's related objects
                version_node = next(
                    (
                        version_node
                        for version_node in self.datasource.version_nodes
                        if version_node.node_id == node_id
                    ),
                    None,
                )
                if not version_node:
                    continue

                rel_path = version_node.relative_path
                ver_id = version_node.version_id

                # Create a Reference object for each chunk
                ref = Reference(
                    content=chunk.text,
                    score=combo_score,
                    relative_path=rel_path,
                    version_display_name=str(
                        ver_id
                    ),  # TODO: should this be vcs_hash instead of the DB id?
                    version_id=ver_id,
                    node_id=node_id,
                    chunk_id=chunk.id,
                    chunk_number=chunk.chunk_number,
                    metadata={},
                    tool_call_id=self.tool_call_id,
                )
                self._references.add_reference(ref)

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=f"{TOOL_ERROR_MESSAGE.wrap(f'No results found for the given search query. {SEARCH_QUERY.wrap(self.search_query)}')}",
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name="HybridSearchTool"
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=f"""HybridSearchTool Results{SEARCH_QUERY.wrap(self.search_query)}{REFERENCE_LIST.wrap(
                "\n".join(
                    f"{REFERENCE.wrap(REFERENCE_CONTENT.wrap(ref.content))}{REFERENCE_RELATIVE_PATH.wrap(ref.version_display_name + '/' + ref.relative_path)}"
                    for ref in self.references
                )
            )}""",
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="HybridSearchTool"
            ),
        )
