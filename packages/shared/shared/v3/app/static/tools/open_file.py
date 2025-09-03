from database.db import get_session
from database.models import ChunkAndEmbedding, ContentKind, DerivedContent
from shared.v3.globals.glossary import (
    REFERENCE,
    REFERENCE_CONTENT,
    REFERENCE_LIST,
    REFERENCE_RELATIVE_PATH,
    TOOL_ERROR_MESSAGE,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference
from sqlalchemy.orm import selectinload
from sqlmodel import select

# TODO: Set the client context so that I can decide if it's too long


class OpenFileTool(LlmTool):
    """
    OpenFileTool is an LlmTool designed to open a file at a given file path
    and display all the content for that file as a single reference.

    Attributes:
        file_path (str): The path to the file to be opened.
    """

    file_path: str

    def _execute(self) -> None:
        with get_session() as session:
            stmt = (
                select(ChunkAndEmbedding)
                .join(DerivedContent)
                .where(
                    DerivedContent.node_id.in_([n.id for n in self.datasource.nodes])
                )
                .where(DerivedContent.relative_path.endswith(self.file_path))
                .where(DerivedContent.content_kind == ContentKind.CODEBASE_FILE)
                .options(selectinload(ChunkAndEmbedding.content))
                .order_by(ChunkAndEmbedding.chunk_number)
            )
            chunks_and_embeddings = session.exec(stmt).all()

        if not chunks_and_embeddings:
            return

        formatted_results = []
        previous_chunk_text = ""
        for chunk in chunks_and_embeddings:
            current_chunk_text = chunk.text
            if previous_chunk_text:
                overlap_length = min(len(previous_chunk_text), len(current_chunk_text))
                for i in range(overlap_length, 0, -1):
                    if previous_chunk_text[-i:] == current_chunk_text[:i]:
                        current_chunk_text = current_chunk_text[i:]
                        break
            formatted_results.append(current_chunk_text)
            previous_chunk_text = chunk.text

        full_text = "\n".join(formatted_results)

        if len(full_text) > 75000:
            full_text = full_text[:75000] + "\n[Content truncated]"

        self._references.add_reference(
            Reference(
                content=full_text,
                score=1.0,
                version_display_name="",
                relative_path=self.file_path,
                version_id=None,
                node_id=None,
                metadata={},
                tool_call_id=self.tool_call_id,
            )
        )

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=f"{TOOL_ERROR_MESSAGE.wrap(f'No content found for file path: {self.file_path}')}",
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name="OpenFileTool"
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=f"""OpenFileTool Results for: {self.file_path}
    {REFERENCE_LIST.wrap(
        "\n".join(
            f"{REFERENCE.wrap(REFERENCE_CONTENT.wrap(ref.content))}{REFERENCE_RELATIVE_PATH.wrap(ref.relative_path)}"
            for ref in self.references
        )
    )}""",
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="OpenFileTool"
            ),
        )
