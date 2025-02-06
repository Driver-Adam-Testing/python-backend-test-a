from pydantic import BaseModel

PROMPT = """

"""
MESSAGE = {"role": "system", "content": PROMPT}


class BlockKindCopyEditorDiagram(BaseModel):
    """
    This class represents a structured response for a copy editor agent that deals with mermaid diagrams,
    which are expected to be in markdown format.

    Attributes:
        diagram_mermaid (str): A markdown representation of the mermaid diagram.
        description (str): a description

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

    def to_markdown(self) -> str:
        """
        Converts the response into a markdown formatted string suitable for mermaid diagrams.

        This method checks if the response already contains the mermaid code block delimiters.
        If the response is already properly formatted, it returns the response as is.
        Otherwise, it wraps the response in mermaid code block delimiters to ensure it is
        correctly formatted for markdown rendering.

        Returns:
            str: A markdown formatted string containing the mermaid diagram.
        """
        diagram_mermaid = self.diagram_mermaid.strip()
        if diagram_mermaid.startswith("```mermaid") and diagram_mermaid.endswith("```"):
            return diagram_mermaid
        return f"```mermaid\n{diagram_mermaid}\n```\n{self.description}"
