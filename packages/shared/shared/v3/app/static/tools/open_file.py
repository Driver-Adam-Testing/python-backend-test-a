from database.db import get_session
from database.models_v1 import ChunkAndEmbedding, DerivedContent
from shared.v3.app.static.messages.constants import (
    REFERENCE_CONTENT_XML_BEGIN,
    REFERENCE_CONTENT_XML_END,
    REFERENCE_PATH_XML_BEGIN,
    REFERENCE_PATH_XML_END,
    REFERENCE_XML_BEGIN,
    REFERENCE_XML_END,
    REFERENCES_XML_BEGIN,
    REFERENCES_XML_END,
    TOOL_ERROR_XML_BEGIN,
    TOOL_ERROR_XML_END,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference
from sqlalchemy.orm import selectinload
from sqlmodel import select


class OpenFileTool(LlmTool):
    """
    OpenFileTool is an LlmTool designed to open a file at a given file path
    and display all the content for that file as a single reference.

    Attributes:
        file_path (str): The path to the file to be opened.
    """

    file_path: str

    def _execute(self) -> LlmMessage:
        try:
            with get_session() as session:
                stmt = (
                    select(ChunkAndEmbedding)
                    .join(DerivedContent)
                    .where(DerivedContent.node_id.in_(self.datasource.node_ids))
                    .options(selectinload(ChunkAndEmbedding.content))
                    .order_by(ChunkAndEmbedding.chunk_number)
                )
                chunks_and_embeddings = session.exec(stmt).all()

            # If there's no content for this file path
            if not chunks_and_embeddings:
                return self._no_content_response()

            formatted_results = []
            previous_chunk_text = ""
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

            # If the file is too long for the model
            if len(full_text) > 75000:
                return self._error_response(
                    "The file is too long. Use a different tool or limit context."
                )

            # Add this entire file as a single reference
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

            return self.to_tool_call_response_message()

        except Exception as e:
            import traceback

            traceback.print_exc()
            return self._error_response(str(e))

    def _no_content_response(self) -> LlmMessage:
        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(
                f"{TOOL_ERROR_XML_BEGIN}No content found for file path: {self.file_path}"
                f"{TOOL_ERROR_XML_END}"
            ),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="OpenFileTool"
            ),
        )

    def _error_response(self, msg: str) -> LlmMessage:
        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(f"{TOOL_ERROR_XML_BEGIN}{msg}{TOOL_ERROR_XML_END}"),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="OpenFileTool"
            ),
        )

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            # if no references were added, respond with error
            return self._no_content_response()

        references_str = "".join(
            f"{REFERENCE_XML_BEGIN}"
            f"{REFERENCE_CONTENT_XML_BEGIN}{ref.content}{REFERENCE_CONTENT_XML_END}"
            f"{REFERENCE_PATH_XML_BEGIN}{ref.relative_path}{REFERENCE_PATH_XML_END}"
            f"{REFERENCE_XML_END}"
            for ref in self._references
        )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=f"""OpenFileTool Results for: {self.file_path}
{REFERENCES_XML_BEGIN}{references_str}{REFERENCES_XML_END}
""".strip(),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="OpenFileTool"
            ),
        )
