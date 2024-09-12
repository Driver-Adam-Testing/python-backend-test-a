from enum import Enum

from database.derived_content_types import DerivedContentTypeNames

from shared.agent.tools.tool_strict import ToolStrict
from shared.pipelines.search import (
    SearchInput,
    search_content_without_session,
)


class SearchTool(ToolStrict):
    """
    SearchTool is a strict tool class for search operations within a content repository of code and technical documentation.

    Attributes:
        search_query (str): The query string.
        content_types (list[SearchToolInputContentType]): Content types to filter the search.
            - source-code: For searching within source code files.
            - codebase-technical-documentation: For searching within technical documentation.
            - pdf-content: For searching within PDF documents.
        search_algorithm (SearchAlgorithm): The search algorithm. Defaults to 'hybrid'.
            - hybrid: Combines keyword and semantic search.
            - semantic: Focuses on meaning and context.
        search_subfolder_paths (list[str], optional): Relative paths to further filter results.
    """

    class SearchToolInputContentType(str, Enum):
        source_code = "source-code"
        technical_documentation = "codebase-technical-documentation"
        pdf_content = "pdf-content"
        # user_generated_files = "user-generated-files"

    class SearchAlgorithm(str, Enum):
        hybrid = "hybrid"
        semantic = "semantic"
        # keyword = "keyword"

    search_query: str
    content_types: list[SearchToolInputContentType]
    search_algorithm: SearchAlgorithm = SearchAlgorithm.hybrid
    search_subfolder_paths: list[str] | None = None

    @property
    def derived_content_types(self):
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
            elif content_type == self.SearchToolInputContentType.user_generated_files:
                derived_content_types.update(
                    [
                        DerivedContentTypeNames.APPLICATION_NOTE.value,
                    ]
                )
        return list(derived_content_types)

    def execute(self, agent):
        # Ensure relative paths are subfolders or files within agent.paths
        agent.scope.authorize(self.search_subfolder_paths)

        search_input = SearchInput(
            query=self.search_query,
            algorithm=self.search_algorithm.value,
            content_type=self.derived_content_types,
            organization_id=agent.scope.organization_id,
            paths=self.search_subfolder_paths,
        )
        results = search_content_without_session(search_input)

        if not results.results:
            return "Search returned no results"
        agent.add_search_results(results)
        formatted_results = []
        for result in results.results:
            content = result.content
            metadata = result.metadata
            content_type = metadata.get("content_type", "")
            relative_path = metadata.get("relative_path", "")

            formatted_result = f"""<result>
                <content>{content}</content>
                <content_type>{content_type}</content_type>
                <path>{relative_path}</path>
            </result>"""
            formatted_results.append(formatted_result.strip())

        return "\n".join(formatted_results)
