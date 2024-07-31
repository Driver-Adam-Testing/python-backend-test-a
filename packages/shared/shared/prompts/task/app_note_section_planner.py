PROMPT = """Your task is to create sections for a detailed technical document called an app note.
This document requires in-depth insights into the technical context, and will expanding on the existing documentation. Before beginning each section of the document, you must thoroughly understand the codebase related to the technical concept.
To achieve this, utilize the following tools to retrieve additional context and think about the context you need in order to describe each section.
After conducting a comprehensive review and analysis using the tools, proceed to save the sections. Think about how many sections would be appropriate. Create and save between one and five sections.
For each section, after thorough research and understanding, save that section. Sections should be directly related to both the technical context and the user request."""

MESSAGE = {"role": "system", "content": PROMPT}
