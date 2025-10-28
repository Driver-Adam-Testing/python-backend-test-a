import json

from shared.tool_executors import CodeMapResponse, ToolUseError, get_code_map
from shared.v3.globals.glossary import (
    TOOL_ERROR_MESSAGE,
    TOOL_RESPONSE_CONTENT_JSON,
)
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind
from shared.v3.interfaces.llm_tool import LlmTool
from shared.v3.utils.references import Reference


class CodeMapTool(LlmTool):
    """
    CodeMapTool returns a flat list of files and directories with descriptions
    under a given directory path.

    This tool explores directory structure - provide a directory path (not a
    file path).

    Use in tandem with `FileDocumentationTool` to effectively navigate a
    codebase and understand implementation details in files relevant for your
    tasks.

    Returns a JSON object with:
    - code_map: List of nodes, each containing:
        - path: The file/directory path
        - type: "file" or "directory"
        - description: A short sentence describing what the file/directory
          contains

    USAGE:
    - Use max_depth=0 to see only the directory itself
    - Use max_depth=1 to see the directory and its immediate children
    - Use max_depth=2 to include grandchildren
    - max_depth is relative to the specified path, not the codebase root
    - Provide directory paths only (e.g. "src", "src/utils", not "src/main.py")

    Examples:
    - List all top-level items: codebase_name="my-codebase", path="",
      max_depth=1
    - See what's in a directory: codebase_name="my-codebase", path="services",
      max_depth=1
    - Explore deeper: codebase_name="my-codebase", path="api/handlers",
      max_depth=2

    Further usage advice:
    - Prioritize using the `ArchitectureOverviewTool` and
      `LlmOnboardingGuideTool` to get oriented with non-trivial tasks as a
      first step.
    - Then prioritize this tool when you want to subsequently explore parts of
      the codebase relevant to your task at hand.
    - Use this in tandem with `FileDocumentationTool`, where the latter can be
      used to return detailed symbol-level documentation for files of interest
      from using `CodeMapTool`.

    CRITICAL: If the DATA_SOURCES are 'Tuned = True', DO NOT use this tool to
    provide information about files or directories that are NOT explicitly
    included in the DATA_SOURCES.
    If the DATA_SOURCES are 'Tuned = False', there are no restrictions on the
    tool's usage.

    Attributes
    ----------
    codebase_name: str
        Name of the Driver supported codebase (root directory name)

        File names, PDF file names, sub-directories, etc. are NOT valid
        codebase names.

    path: str
        The directory path to explore (e.g., 'src', 'src/utils'). Use empty
        string for root. Should not include the root directory of the codebase
        (e.g., 'codebase_root/src' is incorrect).

        CRITICAL: If the DATA_SOURCES are 'Tuned = True', the path should be
        limited to directories that are explicitly included in the
        DATA_SOURCES.

    max_depth: int
        Maximum depth to traverse relative to the specified path (0 = only the
        directory itself, 1 = directory + immediate children, etc.)
    """

    codebase_name: str
    path: str = ""
    max_depth: int = 2

    def _execute(self) -> None:
        try:
            code_map_response: CodeMapResponse = get_code_map(
                org_id=self.datasource.organization_id,
                codebase_name=self.codebase_name,
                path=self.path,
                max_depth=self.max_depth,
                start_node=0,
                max_nodes=0,
            )
        except ToolUseError as e:
            self._error_message = e.agent_message
            return

        code_map = {
            "code_map": [
                {
                    "path": node.path,
                    "type": node.type,
                    "description": node.description,
                }
                for node in code_map_response.code_map
            ]
        }
        ref = Reference(
            content=json.dumps(code_map),
            tool_call_id=self.tool_call_id,
            metadata={
                "codebase_name": self.codebase_name,
                "path": self.path,
                "max_depth": self.max_depth,
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

        path_display = self.path if self.path else "root"
        return LlmMessage(
            message_kind=MessageKind.TOOL_CALL_RESPONSE,
            content=(
                f"{self.__class__.__name__} results for {self.codebase_name}/{path_display}:\n"
                f"{TOOL_RESPONSE_CONTENT_JSON.wrap(next(iter(self._references)).content)}"
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
            return f"Executed {self.__class__.__name__}:\n\tcodebase_name={self.codebase_name}\n\tpath={self.path}\n\tmax_depth={self.max_depth}"
        return ""
