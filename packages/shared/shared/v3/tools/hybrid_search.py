from shared.interfaces.search import SearchAlgorithm
from shared.pipelines.search import SearchInput, search_content_without_session
from shared.v3.messages.llm_message import LlmMessage, MessageKind
from shared.v3.tools.agent_tool import (
    LlmTool,
    LlmToolContext,
    LlmToolReference,
    LlmToolResponse,
)


class HybridSearchTool(LlmTool):
    """
    HybridSearchTool performs a hybrid search combining keyword and semantic search
    within a content repository of code and technical documentation.

    Attributes:
        search_query (str): The query string.
    """

    search_query: str

    def execute(self, tool_context: LlmToolContext) -> LlmToolResponse:
        search_input = SearchInput(
            query=self.search_query,
            algorithm=SearchAlgorithm.HYBRID,
            content_kinds=None,  # TODO: make these selectable
            organization_id=tool_context.datascope.organization_id,
            node_ids=tool_context.datascope.node_ids,
        )
        results = search_content_without_session(search_input)

        if not results.results:
            return HybridSearchToolResponse("Search returned no results", [])

        formatted_results = []
        references = []
        for result in results.results:
            content = result.content
            path = f"{result.version_display_name}/{result.relative_path}"
            formatted_result = f"""<result>
                <content>{content}</content>
                <path>{path}</path>
            </result>"""
            formatted_results.append(formatted_result.strip())
            references.append(LlmToolReference(content=path))

        return HybridSearchToolResponse(
            content="\n".join(formatted_results),
            references=references,
            id=tool_context.tool_call_id,
        )


class HybridSearchToolResponse(LlmToolResponse):
    content: str
    references: list[LlmToolReference]
    id: str

    def to_message(self) -> LlmMessage:
        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL,
            content=self.content,
            name="HybridSearchTool",
            message_id=self.id,
        )

    def to_references(self) -> list[LlmToolReference]:
        return self.references
