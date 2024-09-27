from database.db import get_session
from database.models_v1 import DerivedContent
from sqlalchemy.orm import selectinload
from sqlmodel import select

from shared.agent.agent_base import AgentBase
from shared.agent.tools.tool_strict import ToolStrict


class OpenFileTool(ToolStrict):
    """
    OpenFileTool is a strict tool class designed to open a file at a given file path
    and display all the Content for that file.

    Attributes:
        file_path (str): The path to the file to be opened. PDFs cannot be opened.
    """

    file_path: str

    def execute(self, agent: AgentBase) -> str:
        agent.scope.authorize(self.file_path)

        with get_session() as session:
            derived_content = session.exec(
                select(DerivedContent)
                .where(
                    DerivedContent.relative_path == self.file_path,
                    DerivedContent.content_type.has(type_name="codebase-file"),
                )
                .options(selectinload(DerivedContent.chunks_and_embeds))
            ).first()

            if not derived_content:
                return f"No content found for file path: {self.file_path}"

            chunks_and_embeddings = sorted(
                derived_content.chunks_and_embeds, key=lambda chunk: chunk.chunk_number
            )

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

            return "\n".join(formatted_results)

    @classmethod
    def system_prompt(cls) -> str:
        return """Use the OpenFileTool to read a source code file in it's entirety. File paths must have a known source code extension."""
