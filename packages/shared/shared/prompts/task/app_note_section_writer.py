PROMPT = """Your task is to write a section of a detailed technical document called an app note.
This document requires in-depth insights into the technical context, and should expanding and deepen understandinf of on the existing documentation. Before writing the document, you must thoroughly understand the codebase related to the technical concept.
To achieve this, utilize the following tools to retrieve additional context and think about the context you need in order to describe each section.
After conducting a comprehensive review and analysis using the tools, proceed give a final answer for the section. The final answer should be in markdown.
After thorough research and understanding, stop execution with the full markdown of the section. Sections should be directly related to both the technical context and the user request."""

MESSAGE = {"role": "system", "content": PROMPT}
