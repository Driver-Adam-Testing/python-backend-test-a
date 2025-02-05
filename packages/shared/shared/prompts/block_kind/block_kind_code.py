from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorCodeBlock(BaseModel):
    """
    This class represents a structured response for a copy editor agent that deals with code block snippets,
    which are expected to be formatted as a list of markdown code blocks with the language specified.

    Attributes:
        code_snippets (list[str]): A list of string representations of the code block content.
        descriptions (list[str]): A list of descriptions for each code snippet.

    Code formatting Instructions:
        - Ensure each code block is wrapped in markdown code block delimiters with the appropriate language identifier.
        - Verify that the code is syntactically correct and properly indented.
        - Remove any trailing whitespace or unnecessary blank lines within each code block.
        - Ensure that the language identifier is included immediately after the opening code block delimiter for proper syntax highlighting.
    """

    code_snippets: list[str]
    descriptions: list[str]

    def to_markdown(self) -> str:
        """
        Converts each code snippet into a markdown formatted code block with descriptions.

        This method ensures that each code snippet is wrapped in code block delimiters
        to be correctly formatted for markdown rendering and includes a description.

        Returns:
            str: A single markdown formatted string containing the code blocks
            and their descriptions in the correct order.
        """
        markdown_snippets = []
        for snippet, description in zip(self.code_snippets, self.descriptions):
            stripped_snippet = snippet.strip()
            if stripped_snippet.startswith("```") and stripped_snippet.endswith("```"):
                markdown_snippets.append(f"{description}\n{stripped_snippet}")
            else:
                markdown_snippets.append(f"{description}\n```\n{stripped_snippet}\n```")
        return "\n".join(markdown_snippets)
