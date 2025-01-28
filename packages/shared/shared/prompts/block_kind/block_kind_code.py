from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorCodeBlock(BaseModel):
    """
    This class represents a structured response for a copy editor agent that deals with code block snippets,
    which are expected to be formatted as a single markdown code block with the language specified.

    Attributes:
        response (str): A string representation of the code block content.

    Code formatting Instructions:
        - Ensure the code block is wrapped in markdown code block delimiters with the appropriate language identifier.
        - Verify that the code is syntactically correct and properly indented.
        - Remove any trailing whitespace or unnecessary blank lines within the code block.
        - Ensure that the language identifier is included immediately after the opening code block delimiter for proper syntax highlighting.
    """

    response: str

    def to_markdown(self) -> str:
        """
        Converts the response into a markdown formatted code block.

        This method ensures that the response is wrapped in code block delimiters
        to be correctly formatted for markdown rendering.

        Returns:
            str: A markdown formatted string containing the code block.
        """
        stripped_response = self.response.strip()
        if stripped_response.startswith("```") and stripped_response.endswith("```"):
            return stripped_response
        return f"```\n{stripped_response}\n```"
