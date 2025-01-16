from database.db import get_session
from database.models_v1 import ContentKind, DerivedContent
from database.models_v2 import Node
from sqlmodel import select

from shared.agent.agent_base import AgentBase
from shared.agent.tools.tool_strict import ToolStrict
from shared.interfaces.search import SearchResult, SearchResults


class CodebaseFolderSummaryTool(ToolStrict):
    """
    CodebaseFolderSummaryTool is tool designed to summarize the content
    of a codebase folder at a given directory path. When folders or codebases are given,
    It should be used to gain summarized context of a whole folder or codebase if the folder
    is the root of the codebase. If the assistant history doesn't include searches, this tool should be used for codebases.

    Attributes:
        codebase_directory_path (str): The path to the directory.
    """

    codebase_directory_path: str

    def execute(self, agent: AgentBase) -> str:
        scope = agent.scope.to_child_datascope([self.codebase_directory_path])

        with get_session() as session:
            stmt = (
                select(DerivedContent)
                .join(Node)
                .where(Node.id == scope.node_ids[0])
                .where(DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
            )
            derived_content = session.exec(stmt).first()

            if not derived_content:
                return f"No content found for file path: {self.codebase_directory_path}"

            search_results = []
            formatted_results = []
            for content in derived_content:
                formatted_result = f"""<result>
                    <content>{content.content}</content>
                    <content_type>long_description</content_type>
                    <path>{content.relative_path}</path>
                </result>"""
                formatted_results.append(formatted_result.strip())

                search_result = SearchResult(
                    content=content.content,
                    score=0.0,
                    metadata={
                        "content_type": "long_description",
                        "path": content.relative_path,
                        "relative_path": content.relative_path,
                        "codebase_id": content.codebase_id,
                        "workspace_id": content.workspace_id,
                    },
                )
                search_results.append(search_result)

            agent.add_search_results(SearchResults(results=search_results))
            return "\n".join(formatted_results)

    @classmethod
    def system_prompt(cls) -> str:
        return """If there are any top or second level codebase folders in the searchable paths, use CodebaseFolderSummaryTool on the first iteration."""
