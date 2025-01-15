from enum import Enum

from database.derived_content_types import DerivedContentTypeNames

from shared.agent.agent_base import AgentBase
from shared.agent.tools.tool_strict import ToolStrict
from shared.interfaces.search import SearchAlgorithm
from shared.pipelines.search import (
    SearchInput,
    search_content_without_session,
)


class SearchTool(ToolStrict):
    """
    SearchTool searches within a content repository of code and technical documentation.
    If no results: try again with null, all-types, and hybrid

    Attributes:
        search_query (str): The query string.
        content_types (list[SearchToolInputContentType]): Content types to filter the search.
            - all-types: Great to use for the first search.
            - source-code: Search source code files.
            - codebase-technical-documentation: Search technical documentation.
            - pdf-content: For searching within PDF documents.
        search_algorithm (enum): The search algorithm.
            - HYBRID: Combines keyword and semantic search.
            - SEMANTIC: Focuses on meaning and context. Use english sentences.
            - KEYWORD: searches in the content of files. Use only a single keyword.
        search_subfolder_with_version_paths (list[str], optional): source paths and dirs to search.
            - Use null to search broadly.
    """

    class SearchToolInputContentType(str, Enum):
        all_types = "all-types"
        source_code = "source-code"
        technical_documentation = "codebase-technical-documentation"
        pdf_content = "pdf-content"

    search_query: str
    content_types: list[SearchToolInputContentType]
    search_algorithm: SearchAlgorithm = SearchAlgorithm.HYBRID
    search_subfolder_with_version_paths: list[str] | None = None

    @property
    def derived_content_types(self) -> list[str]:
        derived_content_types = set()
        for content_type in self.content_types:
            if content_type == self.SearchToolInputContentType.source_code:
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.CODEBASE_FILE.value,
                    ]
                )
            elif (
                content_type == self.SearchToolInputContentType.technical_documentation
            ):
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.LONG_DESCRIPTION.value,
                        DerivedContentTypeNames.CHUNK_DESCRIPTIONS.value,
                        DerivedContentTypeNames.SYMBOL.value,
                        DerivedContentTypeNames.PDF_VISUAL_SUMMARY.value,
                        DerivedContentTypeNames.PDF_TEXT_SUMMARY.value,
                        DerivedContentTypeNames.PDF_IMAGE_SUMMARY.value,
                    ]
                )
            elif content_type == self.SearchToolInputContentType.pdf_content:
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.PDF_SUMMARY.value,
                        DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
                        DerivedContentTypeNames.PDF_VISUAL_SUMMARY.value,
                        DerivedContentTypeNames.PDF_TEXT_SUMMARY.value,
                        DerivedContentTypeNames.PDF_IMAGE_SUMMARY.value,
                        DerivedContentTypeNames.PDF_EXTRACTED_TEXT.value,
                        DerivedContentTypeNames.PDF_EXTRACTED_TABLE.value,
                    ]
                )
            elif content_type == self.SearchToolInputContentType.all_types:
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.PDF_SUMMARY.value,
                        DerivedContentTypeNames.SUPPLEMENTAL_DOCUMENT.value,
                        DerivedContentTypeNames.PDF_VISUAL_SUMMARY.value,
                        DerivedContentTypeNames.PDF_TEXT_SUMMARY.value,
                        DerivedContentTypeNames.PDF_IMAGE_SUMMARY.value,
                        DerivedContentTypeNames.PDF_EXTRACTED_TEXT.value,
                        DerivedContentTypeNames.PDF_EXTRACTED_TABLE.value,
                        DerivedContentTypeNames.LONG_DESCRIPTION.value,
                        DerivedContentTypeNames.CHUNK_DESCRIPTIONS.value,
                        DerivedContentTypeNames.SYMBOL.value,
                        DerivedContentTypeNames.CODEBASE_FILE.value,
                    ]
                )
            elif content_type == self.SearchToolInputContentType.user_generated_files:
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.APPLICATION_NOTE.value,
                    ]
                )
        return list(derived_content_types)

    def execute(self, agent: AgentBase) -> str:
        # Ensure relative paths are subfolders or files within agent.paths
        if self.search_subfolder_with_version_paths:
            node_ids = agent.scope.to_child_datascope(
                self.search_subfolder_with_version_paths
            ).node_ids
        else:
            node_ids = agent.scope.node_ids
        search_input = SearchInput(
            query=self.search_query,
            algorithm=self.search_algorithm.value,
            content_kinds=self.derived_content_types,
            organization_id=agent.scope.organization_id,
            node_ids=node_ids,
        )
        results = search_content_without_session(search_input)

        if not results.results:
            return "Search returned no results"
        agent.add_search_results(results)
        formatted_results = []
        for result in results.results:
            content = result.content

            # TODO: add formatting to the interface. This would allow us to share then
            formatted_result = f"""<result>
                <content>{content}</content>
                <path>{result.version_display_name}:{result.relative_path}</path>
            </result>"""
            formatted_results.append(formatted_result.strip())

        return "\n".join(formatted_results)

    @classmethod
    def system_prompt(cls) -> str:
        return """If you don't have enough information about the project to create a response, use SearchTool. Never return a response without Search Results."""
