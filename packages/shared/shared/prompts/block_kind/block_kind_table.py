from shared.interfaces.agents.block_response import BlockResponse

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorTable(BlockResponse):
    """
    This class represents a structured response for a copy editor agent that deals with tables.
    It is designed to encapsulate a table with a header row and subsequent rows, and provide a method
    to convert this table into a markdown format.

    Attributes:
        headers (list[str]): A list of strings representing the column headers of the table.
        rows (list[list[str]]): A list of lists, where each inner list represents a row in the table.

    Usage:
        An agentic system should populate the 'headers' attribute with the column headers and
        the 'rows' attribute with the table rows.
    """

    headers: list[str]
    rows: list[list[str]]
    rationale: str

    def to_markdown(self) -> str:
        header_row = "| " + " | ".join(self.headers) + " |\n"
        separator_row = "| " + " | ".join("---" for _ in self.headers) + " |\n"
        data_rows = "\n".join("| " + " | ".join(row) + " |" for row in self.rows)
        return f"{header_row}{separator_row}{data_rows}"
