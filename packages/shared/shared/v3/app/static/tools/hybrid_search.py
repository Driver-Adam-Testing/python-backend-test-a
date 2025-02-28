from shared.interfaces.search import SearchAlgorithm
from shared.pipelines.search import SearchInput, search_content_without_session
from shared.v3.app.static.messages.constants import (
    REFERENCE_CONTENT_XML_BEGIN,
    REFERENCE_CONTENT_XML_END,
    REFERENCE_PATH_XML_BEGIN,
    REFERENCE_PATH_XML_END,
    REFERENCE_XML_BEGIN,
    REFERENCE_XML_END,
    REFERENCES_XML_BEGIN,
    REFERENCES_XML_END,
    SEARCH_QUERY_XML_BEGIN,
    SEARCH_QUERY_XML_END,
    TOOL_ERROR_XML_BEGIN,
    TOOL_ERROR_XML_END,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import (
    LlmTool,
)
from shared.v3.utils.references import Reference


class HybridSearchTool(LlmTool):
    """
    HybridSearchTool performs a hybrid search combining keyword and semantic search
    within a content repository of code and technical documentation.

    If you do not have external information, you can use this tool to search the codebase.

    Attributes:
        search_query (str): The query string.
    """

    search_query: str

    def _execute(self) -> LlmMessage:
        search_input = SearchInput(
            limit=5,
            query=self.search_query,
            algorithm=SearchAlgorithm.HYBRID,
            content_kinds=None,
            organization_id=self.datascope.organization_id,
            node_ids=self.datascope.node_ids,
        )
        results = search_content_without_session(search_input)

        if not results.results:
            return self.to_tool_call_response_message()
        for result in results.results:
            self._references.add_reference(
                Reference(
                    content=result.content,
                    score=result.score,
                    version_display_name=result.version_display_name,
                    relative_path=result.relative_path,
                    version_id=result.version_id,
                    node_id=result.node_id,
                    metadata=result.metadata,
                    tool_call_id=self.tool_call_id,
                    chunk_id=result.metadata.get("chunk_id", None),
                    chunk_number=result.metadata.get("chunk_number", None),
                )
            )
        return self.to_tool_call_response_message()

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=f"{TOOL_ERROR_XML_BEGIN} No results found for the given search query. {SEARCH_QUERY_XML_BEGIN}{self.search_query}{SEARCH_QUERY_XML_END}{TOOL_ERROR_XML_END}",
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name="HybridSearchTool"
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=f"""HybridSearchTool Results for: {SEARCH_QUERY_XML_BEGIN}{self.search_query}{SEARCH_QUERY_XML_END}{REFERENCES_XML_BEGIN}
                {"".join(f"{REFERENCE_XML_BEGIN}{REFERENCE_CONTENT_XML_BEGIN}{ref.content}{REFERENCE_CONTENT_XML_END}{REFERENCE_PATH_XML_BEGIN}{ref.version_display_name}/{ref.relative_path}{REFERENCE_PATH_XML_END}{REFERENCE_XML_END}" for ref in self.references)}
            {REFERENCES_XML_END}""".strip(),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="HybridSearchTool"
            ),
        )
