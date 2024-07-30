METADATA_SYSTEM_PROMPT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

In particular, you are skilled at describing configuration and metadata files such as markdown, JSON, YAML, Makefiles, etc.
"""

PURPOSE_PROMPT = """
You will be given contents from a metadata or configuration file that is not code, but is from a software codebase.

In a single paragraph of 3 to 5 sentences, explain the purpose of the file contents. Consider questions such as the following when providing your output:

- What kind of file is this? Does it configure other software, hardware, cloud components, contain data used by the application, etc.?
- Does this file provide narrow or broad functionality? If it is narrow, what is that?
- Are there many conceptual categories or components to this file's contents? If so, what is the common theme or purpose?
- What is the relevance of this file's content to a codebase?
"""

CONTENT_SUMMARY_PROMPT = """
You will be given contents from a metadata or configuration file that is not code, but is from a software codebase.

In one or more paragraphs, summarize the functional details of the file's contents that are provided below. Choose a summary length appropriate for the length and complexity of the content. Longer and more complex content should have more summary content.

In writing your content summary, consider the following:
- What are the most important technical details that a developer working with this file should know?
"""

METADATA_TEMPLATE = [
    ("# Overview",),
    ("## Purpose", PURPOSE_PROMPT),
    ("## Content Summary", CONTENT_SUMMARY_PROMPT),
]
