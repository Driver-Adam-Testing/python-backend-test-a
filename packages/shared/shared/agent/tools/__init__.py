from .open_file_tool import OpenFileTool
from .search_tool import SearchTool
from .tool_strict import ToolStrict

TOOL_REGISTRY: dict[str, type[ToolStrict]] = {}
TOOL_REGISTRY[SearchTool.__name__] = SearchTool
TOOL_REGISTRY[OpenFileTool.__name__] = OpenFileTool
