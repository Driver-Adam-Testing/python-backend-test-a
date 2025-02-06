from shared.interfaces.agents.block_response import BlockResponse

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorText(BlockResponse):
    """
    This class represents a structured response for a copy editor agent that deals with paragraphs of text.

    Attributes:
        response (str): A markdown string representing the text content.

    Usage:
        An agentic system should populate the 'response' attribute with the text content.
    """

    response: str

    def to_markdown(self) -> str:
        return self.response
