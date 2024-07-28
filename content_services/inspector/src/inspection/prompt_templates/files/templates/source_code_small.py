SOURCE_CODE_SMALL_SYSTEM_PROMPT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Answer questions such as:

- Does this code provide a narrow and specific functionality, or does it contain broad functionality?
- What kind of code is this? For example, is this code a short script, a collection of global variables or configuration variables, etc.?
"""

SOURCE_CODE_SMALL_TEMPLATE = [
    ("# Overview",),
    ("## Purpose", PURPOSE_PROMPT),
]
