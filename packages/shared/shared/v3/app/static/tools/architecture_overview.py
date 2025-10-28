from shared.tool_executors import ToolUseError, get_architecture_overview
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_MARKDOWN,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class ArchitectureOverviewTool(LlmTool):
    """
    ArchitectureOverviewTool returns a complete architectural overview document
    for the specified codebase in markdown format.

    You should prioritize fetching and reading this content at the beginning of
    any non-trivial task.

    Attributes
    ----------
    codebase_name: str
        Name of the Driver supported codebase (root directory name)

        File names, PDF file names, sub-directories, etc. are NOT valid
        codebase names.
    """

    codebase_name: str

    def _execute(self) -> None:
        try:
            architecture_overview = get_architecture_overview(
                self.datasource.organization_id, self.codebase_name
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        ref = Reference(
            content=architecture_overview,
            tool_call_id=self.tool_call_id,
            metadata={
                "codebase_name": self.codebase_name,
            },
        )
        self._references.add_reference(ref)

    def to_tool_call_response_message(self) -> LlmMessage:
        if not self._references:
            return LlmMessage(
                message_kind=MessageKind.TOOL_CALL_RESPONSE,
                content=TOOL_ERROR_MESSAGE.wrap(self._error_message),
                tool_response=LlmMessage.ToolCallResponse(
                    id=self.tool_call_id or None, name=self.__class__.__name__
                ),
            )

        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(
                f"{self.__class__.__name__} results for {self.codebase_name}:\n"
                f"{TOOL_RESPONSE_CONTENT_MARKDOWN.wrap(next(iter(self._references)).content)}"
            ),
            tool_response=LlmMessage.ToolCallResponse(
                id=self.tool_call_id or None, name=self.__class__.__name__
            ),
        )

    @property
    def status(self) -> str:
        if self._error_message:
            return f"{self.__class__.__name__} failed"
        if self._references:
            return (
                f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}"
        )
        return ""
