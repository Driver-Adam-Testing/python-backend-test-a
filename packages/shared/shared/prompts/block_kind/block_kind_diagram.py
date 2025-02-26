import re

from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorDiagram(BaseModel):
    """
    This class represents a structured response for a copy editor agent that deals with mermaid diagrams,
    which are expected to be in markdown format.

    Attributes:
        diagram_mermaid (str): A markdown representation of the mermaid diagram. IMPORTANT: Ensure that diagram_mermaid is ONLY a single, code fenced, mermaid block.
        description (str): a description of the diagram.

    Mermaid formatting Instructions:
        - Review any mermaid code blocks in this document and correct any errors preventing them from rendering properly.
        - Ensure there are no forbidden characters such as "(" or ")" or double hyphen "--" in the element labels to avoid rendering errors.
        - Ensure that any lists in the mermaid block use the correct syntax. For example:
            Project -->|Contains| ["name", "authors", "date", "version"]
            HardwareModule -->|Contains| ["device", "revision"]
          should be formatted as:
            Project -->|Contains| name["name"] & authors["authors"] & date["date"] & version["version"]
            HardwareModule -->|Contains| device["device"] & revision["revision"]
        - Remove spaces in subgraph names, as spaces prevent the diagram from rendering.
    """

    diagram_mermaid: str
    description: str

    def _extract_mermaid_code(self) -> str:
        """
        Uses a regex to find the first fenced Mermaid code block in the diagram_mermaid
        attribute. Returns just the interior of the code block. If no Mermaid fence is found,
        returns the entire diagram_mermaid string (as a fallback).

        For example, if the diagram_mermaid string looks like:
            'Some text before\n```mermaid\ngraph LR; A-->B\n```\nSome text after'
        Then _extract_mermaid_code() will return: 'graph LR; A-->B'
        """
        content = self.diagram_mermaid.strip()

        # This regex captures everything between ```mermaid and the next ```
        pattern = re.compile(r"(?s)```mermaid(.*?)```")
        match = pattern.search(content)
        if match:
            # Return the code between ```mermaid and ```
            return match.group(1).strip()
        # If no match, return the entire string as a fallback
        return content

    def to_markdown(self) -> str:
        """
        Returns the Mermaid diagram in a markdown fenced code block.

        1) Find the code inside the first Mermaid fence (if it exists).
        2) Wrap the resulting code in a proper code fence.
        """
        code = self._extract_mermaid_code()
        return f"```mermaid\n{code}\n```"

    def to_mermaid_interior_string(self) -> str:
        """
        Returns just the raw mermaid code string (no triple-backtick fences).
        """
        return self._extract_mermaid_code()
