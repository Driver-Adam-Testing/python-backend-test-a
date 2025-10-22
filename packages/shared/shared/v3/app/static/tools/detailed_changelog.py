from shared.tool_executors import ToolUseError, get_detailed_changelog
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_YAML,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class DetailedChangelogTool(LlmTool):
    """
    DetailedChangelogTool returns the detailed changelog for a specific year
    and month of the given codebase in YAML format.

    Use this when more detailed information about the development process of
    the codebase at a specific time might be helpful.

    Attributes
    ----------
    codebase_name: str
        Name of the Driver supported codebase.
    year: str
        The year of the changelog (e.g. "2023").
    month: str
        The month of the changelog (e.g. "01", "02", ..., "12").
    """

    codebase_name: str
    year: str
    month: str

    def _execute(self) -> None:
        try:
            detailed_changelog = get_detailed_changelog(
                self.datasource.organization_id,
                self.codebase_name,
                self.year,
                self.month,
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        ref = Reference(
            content=detailed_changelog,
            tool_call_id=self.tool_call_id,
            metadata={
                "codebase_name": self.codebase_name,
                "year": self.year,
                "month": self.month,
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
                f"{self.__class__.__name__} results for {self.codebase_name} {self.year}-{self.month}:\n"
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
            return f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}\n\tyear={self.year}\n\tmonth={self.month}"
        return ""
