from inspection.prompt_templates.files.templates.metadata_default import (
    METADATA_SYSTEM_PROMPT,
)
from utils.templates import S

PURPOSE_PROMPT = """
You will be given contents from a metadata or configuration file that is not code, but is from a software codebase.

In a single paragraph of 3 to 5 sentences, explain the purpose of the file contents. Consider questions such as the following when providing your output:

- What kind of file is this? Does it configure other software, hardware, cloud components, contain data used by the application, etc.?
- Does this file provide narrow or broad functionality? If it is narrow, what is that?
- Are there many conceptual categories or components to this file's contents? If so, what is the common theme or purpose?
- What is the relevance of this file's content to a codebase?
"""

PURPOSE_FROM_CHUNKS = """
You will be provided two or more paragraphs describing the purpose of overlapping chunks of a metadata or configuration file.

In a single paragraph of 3 to 5 sentences, combine the multiple purpose paragraphs into a single cohesive paragraph that describes the purpose of the entire file.
"""

CONTENT_SUMMARY_PROMPT = """
You will be given contents from a metadata or configuration file that is not code, but is from a software codebase.

In one or more paragraphs, summarize the functional details of the file's contents that are provided below. Choose a summary length appropriate for the length and complexity of the content. Longer and more complex content should have more summary content.

In writing your content summary, consider the following:
- What are the most important technical details that a developer working with this file should know?
"""

CONTENT_SUMMARY_FROM_CHUNKS = """
You will be provided two or more paragraphs describing the content summary of overlapping chunks of a metadata or configuration file.

In one or more paragraphs, combine the multiple technical summary paragraphs into one or more cohesive paragraphs that describes the technical content of the entire file.
"""

METADATA_MULTI_CONTEXT_TEMPLATE = [
    (S.RAW, "# Overview"),
    (
        S.MULTI_PROMPT_TEXT,
        "## Purpose",
        METADATA_SYSTEM_PROMPT,
        PURPOSE_PROMPT,
        PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_PROMPT_TEXT,
        "## Content Summary",
        METADATA_SYSTEM_PROMPT,
        CONTENT_SUMMARY_PROMPT,
        CONTENT_SUMMARY_FROM_CHUNKS,
    ),
]
