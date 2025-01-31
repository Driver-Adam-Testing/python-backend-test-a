import enum

from shared.interfaces.agents.block_response import BlockResponse

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorList(BlockResponse):
    """
    This class represents a structured response for a copy editor agent that deals with lists.
    It is designed to encapsulate a list of strings and provide a method to convert this list
    into a markdown format. The class supports two types of lists: ordered and unordered.

    Attributes:
        response (list[str]): A list of strings representing the items in the list.
        list_kind (ListKind): An enumeration indicating whether the list is ordered or unordered.

    ListKind (enum.Enum): An enumeration with two possible values:
        - ORDERED: Represents an ordered list where each item is prefixed with a number.
        - UNORDERED: Represents an unordered list where each item is prefixed with a bullet point.

    Usage:
        An agentic system should populate the 'response' attribute with the list items and
        set the 'list_kind' attribute to either ListKind.ORDERED or ListKind.UNORDERED based
        on the desired output format.
    """

    class ListKind(str, enum.Enum):
        ORDERED = "ORDERED"
        UNORDERED = "UNORDERED"

    list_output: list[str]
    list_kind: ListKind
    rationale: str

    def to_markdown(self) -> str:
        if self.list_output == self.ListKind.ORDERED:
            return "\n".join(
                f"{i+1}. {item}" for i, item in enumerate(self.list_output)
            )
        else:
            return "\n".join(f"- {item}" for item in self.list_output)
