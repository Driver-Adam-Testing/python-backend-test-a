from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorCodeBlock(BaseModel):
    """
    This class is designed to generate a structured response for a copy editor agent that processes code block snippets.
    The output is expected to be formatted as a list of markdown code blocks, each with a specified language identifier.

    Attributes:
        code_snippets (list[str]): A list containing the code snippets to be formatted.
        descriptions (list[str]): A corresponding list of descriptions for each code snippet, maintaining the same order. (can be a header, paragraph text, descriptive lists, etc.)

    Code Formatting Instructions:
        - Each code block must be enclosed within markdown code block delimiters (```) with the appropriate language identifier immediately following the opening delimiter.
        - The code within each block should be syntactically correct and properly indented to ensure readability and accuracy.
        - Eliminate any trailing whitespace or unnecessary blank lines within each code block to maintain a clean format.
        - The language identifier is crucial for syntax highlighting and must be included right after the opening code block delimiter.
    """

    code_snippets: list[str]
    descriptions: list[str]

    def to_markdown(self) -> str:
        """
        Transforms each code snippet into a markdown formatted code block, paired with its corresponding description.

        This method ensures that each code snippet is properly wrapped in code block delimiters for markdown rendering,
        and is accompanied by its description in the specified order.

        Returns:
            str: A single markdown formatted string that contains the code blocks and their descriptions,
            arranged in the correct sequence as described in the desired output format.
        """
        markdown_snippets = []
        for snippet, description in zip(self.code_snippets, self.descriptions):
            stripped_snippet = snippet.strip()
            markdown_snippets.append(f"{description}\n{stripped_snippet}\n")
        return "\n".join(markdown_snippets)
