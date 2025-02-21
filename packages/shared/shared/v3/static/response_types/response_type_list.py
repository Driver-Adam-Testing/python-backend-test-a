from shared.v3.interfaces.llm_response_type import LlmResponseType


class ListResponse(LlmResponseType):
    """
    ListResponse is a response type that can be used to generate a list of items.
    response: A markdown response of the list of items to be displayed.
    rationale: The rationale for creating and formatting the list in the way it is.
    """

    list_formatted_response: str
    rationale: str

    def to_markdown(self) -> str:
        return self.list_formatted_response
