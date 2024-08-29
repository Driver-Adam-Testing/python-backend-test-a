from enum import Enum

from pydantic import BaseModel

from shared.pipelines.search import (
    SearchInput,
    SearchResults,
    search_content_without_session,
)


def format_search_results(results: SearchResults):
    if not results.results:
        return "Search returned no results"

    formatted_results = []
    for result in results.results:
        content = result.content
        metadata = result.metadata
        content_type = metadata.get("content_type", "")
        relative_path = metadata.get("relative_path", "")

        formatted_result = f"""<result>
            <content>{content}</content>
            <content_type>{content_type}</content_type>
            <relative_path>{relative_path}</relative_path>
        </result>"""
        formatted_results.append(formatted_result.strip())

    return "\n".join(formatted_results)


class SearchToolInputContentType(str, Enum):
    source_code = "codebase-file"


class SearchToolInput(BaseModel):
    search_query: str
    content_types: list[SearchToolInputContentType]

    def execute(self, agent):
        print(agent, self)
        search_input = SearchInput(
            query=self.search_query,
            algorithm="hybrid",
            content_type=self.content_types,
            organization_id=agent.organization_id,
            paths=agent.paths,
        )
        return format_search_results(search_content_without_session(search_input))


def to_tool_call_input(tool_call):
    print(tool_call)
    tool_call_type = tool_call.get("type")
    if tool_call_type == "function":
        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["parsed_arguments"]

        if function_name in globals() and issubclass(
            globals()[function_name], BaseModel
        ):
            return globals()[function_name](**arguments)

    raise ValueError(
        f"Unsupported tool call type or function name: {tool_call_type}, {function_name}"
    )
