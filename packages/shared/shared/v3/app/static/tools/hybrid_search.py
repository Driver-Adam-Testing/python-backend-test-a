from database.db import get_session
from database.models_v1 import ChunkAndEmbedding, DerivedContent
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
from sqlmodel import select


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
            results = session.exec(
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
                        [node.id for node in self.datasource.nodes]
                    )
                )
                .order_by("semantic_score")
                .limit(50)
            ).all()

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
                node = next(
                    (node for node in self.datasource.nodes if node.id == node_id), None
                )
                if not node:
                    continue

                rel_path = node.relative_path
                ver_id = node.version_id

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

    @property
    def status(self) -> LlmTool.LlmToolStatusString:
        if self._references:
            unique_short_paths = {ref.short_path for ref in self.references}
            return f"Found references for {self.search_query}\n{"\n".join(unique_short_paths)}"
        return f"Searching: {self.search_query}...\n"
