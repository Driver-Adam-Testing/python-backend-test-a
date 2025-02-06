from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorAny(BaseModel):
    """
    This class represents a structured response for a copy editor agent that deals with any type of content,
    which is expected to be in markdown format.

    Attributes:
        response (str): A markdown representation of the content.
    """

    response: str

    def to_markdown(self) -> str:
        return self.response
