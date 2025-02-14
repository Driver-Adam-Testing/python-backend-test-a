from shared.interfaces.search import SearchAlgorithm
from shared.pipelines.search import SearchInput, search_content_without_session
from shared.v3.agents.agent_tool import (
    LlmTool,
    LlmToolContext,
    ToolReference,
)
from shared.v3.messages.llm_message import LlmMessage, MessageKind
from shared.v3.static.messages.global_message_constants import (
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


class HybridSearchTool(LlmTool):
    """
    HybridSearchTool performs a hybrid search combining keyword and semantic search
    within a content repository of code and technical documentation.

    If you do not have external information, you can use this tool to search the codebase.

    Attributes:
        search_query (str): The query string.
    """

    search_query: str

    def execute(self, tool_context: LlmToolContext) -> LlmMessage:
        self._tool_context = tool_context
        search_input = SearchInput(
            query=self.search_query,
            algorithm=SearchAlgorithm.HYBRID,
            content_kinds=None,
            organization_id=tool_context.datascope.organization_id,
            node_ids=tool_context.datascope.node_ids,
        )
        results = search_content_without_session(search_input)

        if not results.results:
            self._references = []
            return self
        references = []
        for result in results.results:
            references.append(
                ToolReference(
                    content=result.content,
                    score=result.score,
                    version_display_name=result.version_display_name,
                    relative_path=result.relative_path,
                    version_id=result.version_id,
                    node_id=result.node_id,
                    metadata=result.metadata,
                )
            )

        self._references = references
        return self.to_message()

    def to_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=f"{TOOL_ERROR_XML_BEGIN} No results found for the given search query. {SEARCH_QUERY_XML_BEGIN}{self.search_query}{SEARCH_QUERY_XML_END}{TOOL_ERROR_XML_END}",
                tool_response=LlmMessage.ToolCallResponse(
                    id=self._tool_context.tool_call_id or None, name="HybridSearchTool"
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=f"""HybridSearchTool Results for: {SEARCH_QUERY_XML_BEGIN}{self.search_query}{SEARCH_QUERY_XML_END}{REFERENCES_XML_BEGIN}
                {"".join(f"{REFERENCE_XML_BEGIN}{REFERENCE_CONTENT_XML_BEGIN}{ref.content}{REFERENCE_CONTENT_XML_END}{REFERENCE_PATH_XML_BEGIN}{ref.version_display_name}/{ref.relative_path}{REFERENCE_PATH_XML_END}{REFERENCE_XML_END}" for ref in self._references)}
            {REFERENCES_XML_END}""".strip(),
            tool_response=LlmMessage.ToolCallResponse(
                id=self._tool_context.tool_call_id or None, name="HybridSearchTool"
            ),
        )
