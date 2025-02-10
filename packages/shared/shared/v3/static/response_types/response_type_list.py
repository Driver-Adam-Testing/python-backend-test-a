import enum

from shared.v3.utils.parseable import LlmParseable


class ListResponse(LlmParseable):
    """
    ListResponse is a structured response type for a copy editor agent that handles lists.
    It encapsulates a list of strings and provides a method to convert this list into a
    markdown format. The class supports two types of lists: ordered and unordered.

    Attributes:
        list_elements (list[str]): A list of strings representing the items in the list.
        list_kind (ListKind): An enumeration indicating whether the list is ordered or unordered.
        rationale (str): A string explaining the reasoning or purpose behind the list.

    ListKind (enum.Enum): An enumeration with two possible values:
        - ORDERED: Represents an ordered list where each item is prefixed with a number.
        - UNORDERED: Represents an unordered list where each item is prefixed with a bullet point.

    Usage:
        Populate the 'list_elements' attribute with the list items, set the 'list_kind'
        attribute to either ListKind.ORDERED or ListKind.UNORDERED based on the desired output format,
        and provide a 'rationale' explaining the purpose of the list.
    """

    class ListKind(str, enum.Enum):
        ORDERED = "ORDERED"
        UNORDERED = "UNORDERED"

    list_elements: list[str]
    list_kind: ListKind
    rationale: str

    def to_markdown(self) -> str:
        if self.list_output == self.ListKind.ORDERED:
            return "\n".join(
                f"{i+1}. {item}" for i, item in enumerate(self.list_output)
            )
        else:
            return "\n".join(f"- {item}" for item in self.list_output)

    # @classmethod
    # def to_instruction_string(cls) -> str:
    #     return f"""
    #     Please format your response as a JSON object that can be parsed into a pydantic BaseModel instance of the following class:

    #     {cls.__doc__}

    #     Example JSON object:
    #     {{
    #         "list_elements": ["Item 1", "Item 2", "Item 3"],
    #         "list_kind": "UNORDERED",
    #         "rationale": "This is an example rationale explaining the purpose of the list."
    #     }}
    #     """
