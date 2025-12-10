from database.db import get_session
from database.models import ChunkAndEmbedding, DerivedContent
from sqlalchemy.orm import selectinload
from sqlmodel import select

from shared.agent.agent_base import AgentBase
from shared.agent.tools.tool_strict import ToolStrict
from shared.interfaces.search import SearchResult, SearchResults


class OpenFileTool(ToolStrict):
    """
    OpenFileTool is a strict tool class designed to open a file at a given file path
    and display all the Content for that file.

    Attributes:
        file_path (str): The path to the file to be opened. PDFs cannot be opened.
    """

    file_path: str

    def execute(self, agent: AgentBase) -> str:
        try:
            datascope = agent.scope.to_child_datascope([self.file_path])

            with get_session() as session:
                stmt = (
                    select(ChunkAndEmbedding)
                    .join(DerivedContent)
                    .where(DerivedContent.node_id == datascope.node_ids[0])
                    .options(selectinload(ChunkAndEmbedding.content))
                    .order_by(ChunkAndEmbedding.chunk_number)
                )
                chunks_and_embeddings = session.exec(stmt).all()

            if not chunks_and_embeddings:
                return f"No content found for file path: {self.file_path}"

            formatted_results = []
            previous_chunk_text = ""

            # TODO: this function takes chunks and reformats them into a full document. There could be better ways to do this.
            for chunk in chunks_and_embeddings:
                current_chunk_text = chunk.text
                if previous_chunk_text:
                    overlap_length = min(
                        len(previous_chunk_text), len(current_chunk_text)
                    )
                    for i in range(overlap_length, 0, -1):
                        if previous_chunk_text[-i:] == current_chunk_text[:i]:
                            current_chunk_text = current_chunk_text[i:]
                            break
                formatted_results.append(current_chunk_text)
                previous_chunk_text = chunk.text

            full_text = "\n".join(formatted_results)

            # TODO: Make this limit model dependent
            # TODO: Will become irrelevant when tool response lengths are optimized across all tools.
            if len(full_text) > 75000:
                raise Exception(
                    "The file is too long. Use the SearchTool to return relevant context."
                )

            version_display_name = (
                datascope.nodes[0].version.vcs_hash
                if datascope.nodes[0].version.vcs_hash
                else "Unversioned"
            )
            search_result = SearchResult(
                content=full_text,
                score=1.0,
                relative_path=datascope.nodes[0].node.relative_path,
                version_display_name=version_display_name,
                node_id=datascope.nodes[0].node.id,
                version_id=datascope.nodes[0].node.version_id,
                metadata={},
            )
            agent.add_search_results(SearchResults(results=[search_result]))

            return full_text
        except Exception:
            import traceback

            traceback.print_exc()
            raise


@classmethod
def system_prompt(cls: any) -> str:
    return """Use the OpenFileTool to read a source code file in it's entirety. File paths must have a known source code extension."""
