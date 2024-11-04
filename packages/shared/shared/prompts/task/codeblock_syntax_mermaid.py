PROMPT = """Please review the mermaid code block in this document and correct any errors preventing it from rendering properly.
Ensure the syntax and formatting comply with Mermaid's guidelines so the diagram displays as intended.
Ensure there are no forbidden characters such as "(" or ")" or double hyphen "--" in the element labels to avoid rendering errors.

Ensure that any conains lists in the mermaid block use the correct syntax for example:
    ...
    Project -->|Contains| ["name", "authors", "date", "version"]
    HardwareModule -->|Contains| ["device", "revision"]
    ...
would become
    ...
    Project -->|Contains| name["name"] & authors["authors"] & date["date"] & version["version"]
    HardwareModule -->|Contains| device["device"] & revision["revision"]
    ...
Remove spaces in subgraph names, spaces in subgraph names prevent the diagram from rendering.
"""

MESSAGE = {"role": "system", "content": PROMPT}
