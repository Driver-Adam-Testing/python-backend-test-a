SOURCE_CODE_LARGE_SYSTEM_PROMPT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Answer questions such as:

- Does this code provide a narrow and specific functionality, or does it contain broad functionality?
- Is this code a collection of many different components? If so, what is the common them or purpose?
- What kind of code is this? For example, is this code clearly an executable script, a library intended to be imported elsewhere, does it define public APIs, etc.?
"""

TECHNICAL_SUMMARY_PROMPT = """
In one or more paragraphs, summarize the important technical concepts of the code provided below. Choose a summary length appropriate for the length and complexity of code. Longer and more complex code should have more summary content.

In writing your technical summary, consider the following:
- What are the most important technical concepts and details that a developer working with this could should know.
- Write more about about the conceptual use cases, applications, and logic of how components of the code are used instead of focusing on particular functions, classes, variables, etc.
"""

IMPORTS_PROMPT = """
Summarize the dependencies or imports used in the code provided below.

- If there are none, just say so.
- Do not speculate on the nature of the imports or dependencies if it is not clear what they are for. If it is not clear, just identify the name. If it is clear what an import or dependency is, briefly describe it.
"""

DATA_STRUCTURES_PROMPT = """
Summarize the data structures in the code provided below.

- If there are none, just say so.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important data structures.
- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a data structure.
"""

FUNCTIONS_PROMPT = """
Summarize the functions or methods in the code provided below. For each function or method, describe the inputs, control flow and logic, and output.

- If there are none, just say so.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important functions or methods.
- If you are describing a method of a class rather than a free function, identify the class the method is associated with when you describe it.
- When describing a function or method, provide detail that matches the complexity of the function or method body. Large and complex functions or methods should get longer explanations, while small ones much less.
- Provide your output such that each function or method is described in a 3rd level markdown header where the function or method name is the header title (e.g., ### <function_name>).
"""

DIAGRAMS_PROMPT = """
Build an ASCII diagram that represents the logical flow of the code provided below.
"""

SOURCE_CODE_LARGE_TEMPLATE = [
    ("# Overview",),
    ("## Purpose", PURPOSE_PROMPT),
    ("## Technical Summary", TECHNICAL_SUMMARY_PROMPT),
    ("## Imports and Dependencies", IMPORTS_PROMPT),
    ("## Data Structures", DATA_STRUCTURES_PROMPT),
    ("## Functions", FUNCTIONS_PROMPT),
    # ("## Diagram", DIAGRAMS_PROMPT),
]
