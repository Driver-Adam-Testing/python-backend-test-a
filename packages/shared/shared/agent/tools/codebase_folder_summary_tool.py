from database.db import get_session
from database.models import DerivedContent, Node, Version, VersionNode
from database.models_enums import ContentKind
from sqlalchemy.orm import selectinload
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

        if not scope.version_node_ids:
            return f"No content found for file path: {self.codebase_directory_path}"

        with get_session() as session:
            # First get the VersionNode to access version information
            version_node_stmt = (
                select(VersionNode)
                .options(selectinload(VersionNode.version))
                .where(VersionNode.id == scope.version_node_ids[0])
            )
            version_node = session.exec(version_node_stmt).first()

            stmt = (
                select(DerivedContent)
                .join(Node, DerivedContent.node_id == Node.id)
                .join(VersionNode, VersionNode.node_id == Node.id)
                .options(selectinload(DerivedContent.node))
                .where(VersionNode.id == scope.version_node_ids[0])
                .where(
                    (DerivedContent.content_kind == ContentKind.LONG_DESCRIPTION)
                    | (
                        DerivedContent.content_kind
                        == ContentKind.TOP_LEVEL_LONG_DESCRIPTION
                    )
                )
            )

            # Fetch all matching rows
            derived_contents = session.exec(stmt).all()

            search_results = []
            formatted_results = []

            # Iterate over all results
            version_display_name = (
                version_node.version.vcs_hash
                if version_node.version.vcs_hash
                else "Unversioned"
            )

            for content in derived_contents:
                formatted_result = f"""<result>
        <content>{content.content}</content>
        <content_type>long_description</content_type>
        <path>{version_display_name}/{version_node.relative_path}</path>
    </result>""".strip()
                formatted_results.append(formatted_result)

                search_result = SearchResult(
                    content=content.content,
                    score=0.0,
                    relative_path=version_node.relative_path,
                    version_display_name=version_display_name,
                    version_node_id=content.node.id,
                    version_id=version_node.version_id,
                    metadata={"content_type": content.content_kind},
                )
                search_results.append(search_result)

            # Add the aggregated results to the Agent
            agent.add_search_results(SearchResults(results=search_results))

            # Return the joined summaries
            return "\n".join(formatted_results)

    @classmethod
    def system_prompt(cls) -> str:
        return """If there are any top or second level codebase folders in the searchable paths, use CodebaseFolderSummaryTool on the first iteration."""
