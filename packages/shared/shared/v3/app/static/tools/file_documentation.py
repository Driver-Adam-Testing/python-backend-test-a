from shared.tool_executors import (
    FileDocumentationPayload,
    ToolUseError,
    get_file_documentation,
)
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_MARKDOWN,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class FileDocumentationTool(LlmTool):
    """
    FileDocumentationTool returns detailed symbol-level documentation for a
    specific file in a codebase in markdown format.

    Use in tandem with `CodeMapTool` to effectively navigate a codebase and
    understand implementation details in files relevant for your tasks.

    Attributes
    ----------
    codebase_name: str
        Name of the Driver supported codebase.
    path: str
        The file path to get documentation. Should not include the root
        directory of the codebase (e.g., 'codebase_root/src' is incorrect).
    """

    codebase_name: str
    path: str

    def _execute(self) -> None:
        try:
            file_documentation_response: FileDocumentationPayload = (
                get_file_documentation(
                    org_id=self.datasource.organization_id,
                    codebase_name=self.codebase_name,
                    path=self.path,
                    start_line=1,
                    max_lines=0,
                )
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        ref = Reference(
            content=file_documentation_response.content,
            tool_call_id=self.tool_call_id,
            metadata={
                "codebase_name": self.codebase_name,
                "path": self.path,
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
                f"{self.__class__.__name__} results for {self.codebase_name}/{self.path}:\n"
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
            return f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}\n\tpath={self.path}"
        return ""
