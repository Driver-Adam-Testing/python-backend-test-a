from shared.tool_executors import ToolUseError, get_changelog
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_YAML,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class ChangelogTool(LlmTool):
    """
    ChangelogTool fetches the complete high-level changelog for a codebase,
    broken down by year and month.

    Helpful for orienting and reasoning about a codebase -- use this in any
    context where the historical development process and decisions might be
    helpful. Prioritize calling this at the beginning of a task.

    This tool will return a YAML-formatted changelog organized by year and
    month with high-level feature descriptions and bug fixes for each time
    period.

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
            changelog = get_changelog(
                self.datasource.organization_id,
                self.codebase_name,
                self.datasource.user_id,
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        ref = Reference(
            content=changelog,
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
                f"{TOOL_RESPONSE_CONTENT_YAML.wrap(next(iter(self._references)).content)}"
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
            return f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}"
        return ""
