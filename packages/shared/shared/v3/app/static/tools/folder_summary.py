from database.db import get_session
from database.models import DerivedContent
from database.models_enums import ContentKind
from shared.v3.globals.glossary import (
    REFERENCE,
    REFERENCE_CONTENT,
    REFERENCE_LIST,
    REFERENCE_RELATIVE_PATH,
    SEARCH_QUERY,
    TOOL_ERROR_MESSAGE,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference
from sqlmodel import select


class FolderSummaryTool(LlmTool):
    """
    FolderSummaryTool returns longdescription summaries for a given folder
    (typically the root of a codebase) in the new architecture.

    Exampleusage heuristic (in a systemprompt or rubric):
        “If no searches have been run and a top or secondlevel folder
         is in scope, call FolderSummaryTool on that folder to prime context.”

    Attributes
    ----------
    folder_path : str
        Relative path to the folder you want summarized.
    """

    folder_path: str

    # --------------------------------------------------------------------- #
    # Internal execution                                                    #
    # --------------------------------------------------------------------- #

    def _execute(self) -> None:
        """
        Gather LONG_DESCRIPTION / TOP_LEVEL_LONG_DESCRIPTION content that
        belongs to the folder in `folder_path` and convert each match into
        a Reference so the assistant can cite it later.
        """
        with get_session() as session:
            version_node_lookup = {
                vn.node_id: vn for vn in self.datasource.version_nodes
            }

            matching_node_ids = [
                vn.node_id
                for vn in self.datasource.version_nodes
                if vn.relative_path.endswith(self.folder_path)
            ]

            # Pull derived content for the target folder in one shot.
            rows = session.exec(
                select(DerivedContent)
                .filter(
                    DerivedContent.content_kind.in_(
                        [
                            ContentKind.LONG_DESCRIPTION,
                            ContentKind.TOP_LEVEL_LONG_DESCRIPTION,
                        ]
                    ),
                    DerivedContent.node_id.in_(matching_node_ids),
                )
                .all()
            )

            if not rows:
                return

            for dc in rows:
                version_node = version_node_lookup.get(dc.node_id)
                if not version_node:
                    continue

                version_display_name = (
                    version_node.version.vcs_hash
                    if version_node.version.vcs_hash
                    else "Unversioned"
                )
                ref = Reference(
                    content=dc.content,
                    score=0.0,
                    relative_path=version_node.relative_path,
                    version_display_name=version_display_name,
                    version_id=version_node.version_id,
                    node_id=dc.node_id,
                    chunk_id=None,
                    chunk_number=None,
                    metadata={"content_type": dc.content_kind},
                    tool_call_id=self.tool_call_id,
                )
                self._references.add_reference(ref)

    def to_tool_call_response_message(self) -> LlmMessage:
        """
        Build the assistant visible response in glossary wrapped format.
        """
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=TOOL_ERROR_MESSAGE.wrap(
                    f"No summaries found for folder: {self.folder_path} "
                    f"{SEARCH_QUERY.wrap(self.folder_path)}"
                ),
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name="FolderSummaryTool"
                ),
            )

        # Create a compact list of each summary with its path.
        refs_serialised = "\n".join(
            f"{REFERENCE.wrap(REFERENCE_CONTENT.wrap(r.content))}"
            f"{REFERENCE_RELATIVE_PATH.wrap(r.version_display_name + '/' + r.relative_path)}"
            for r in self.references
        )
        if len(refs_serialised) > 75000:
            refs_serialised = refs_serialised[:75000]
            self._error_message = "The folder summary is too long. Only the first 75000 characters are included."

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(
                f"FolderSummaryTool Results for {SEARCH_QUERY.wrap(self.folder_path)}"
                f"{REFERENCE_LIST.wrap(refs_serialised)}"
            ),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name="FolderSummaryTool"
            ),
        )

    @property
    def status(self) -> LlmTool.LlmToolStatusString:
        if self._references:
            unique_paths = {ref.short_path for ref in self.references}
            if unique_paths:
                return "Folder summaries ready:\n" + "\n".join(unique_paths)
        return f"Summarizing folder: {self.folder_path}…\n"
