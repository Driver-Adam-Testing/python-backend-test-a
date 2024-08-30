from database.db import get_session
from database.models_v1 import DerivedContent
from sqlalchemy.orm import selectinload
from sqlmodel import select

from shared.agent.tools.tool_strict import ToolStrict


class OpenFileTool(ToolStrict):
    """
    OpenFileTool is a strict tool class designed to open a file at a given file path
    and display all the Content for that file.

    Attributes:
        file_path (str): The path to the file to be opened.
    """

    file_path: str

    def execute(self, agent):
        if not any(self.file_path.startswith(base_path) for base_path in agent.paths):
            return f"File path {self.file_path} is not within the allowed paths."

        with get_session() as session:
            derived_content = session.exec(
                select(DerivedContent)
                .where(
                    DerivedContent.relative_path == self.file_path,
                    DerivedContent.content_type == "codebase-file",
                )
                .options(selectinload(DerivedContent.chunks_and_embeds))
            ).first()

            if not derived_content:
                return f"No derived content found for file path: {self.file_path}"

            chunks_and_embeddings = derived_content.chunks_and_embeds

            if not chunks_and_embeddings:
                return f"No chunks and embeddings found for file path: {self.file_path}"

            formatted_results = []
            for chunk in chunks_and_embeddings:
                formatted_result = f"""<chunk>
                    <text>{chunk.text}</text>
                </chunk>"""
                formatted_results.append(formatted_result.strip())

            return "\n".join(formatted_results)
