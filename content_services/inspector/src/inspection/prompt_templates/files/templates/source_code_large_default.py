SOURCE_CODE_LARGE_SYSTEM_PROMPT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable script, a C header file, a library intended to be imported elsewhere, does it define public APIs, etc.?
"""

TECHNICAL_SUMMARY_PROMPT = """
In one or more paragraphs, summarize the important technical concepts of the code provided below. Choose a summary length appropriate for the length and complexity of code. Longer and more complex code should have more summary content.

In writing your technical summary, write about about the conceptual use cases, applications, logic, and component interactions in the code instead of focusing on particular functions, classes, variables, etc. A new developer can read your output and conceptually understand the core technical elements of the code before diving into source code.
"""

IMPORTS_PROMPT = """
Summarize the dependencies or imports used in the code provided below.

- If there are no dependencies or imports, just say so and do not write anything else.
- Do not speculate on the nature of the imports or dependencies if it is not clear what they are for. If it is not clear, just identify the name. If it is clear what an import or dependency is, briefly describe it.
"""

DATA_STRUCTURES_CHECKER = """
Your job is to determine if there are any important data structures defined in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- An important data structure is a custom, complex, or compound data structure in the language of the provided code but does not include primitive types inherent to the programming language such as integers, floating point values, or strings.
- You are only looking for important data structures that are fully defined in the code given to you. For example, a struct or class that is defined in the code. If a data structure is imported or used without being defined in the code, it is not to be considered.

**You only respond with the text 'true' or 'false'.**
- If there is one or more data structure, as described above, respond with 'true'.
- Otherwise, respond with 'false'.
"""

DATA_STRUCTURES_FOUND_PROMPT = """
Summarize the important data structures in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- Only discuss custom, complex, or compound data structures defined in the code below. Do not talk about the most primitive types inherent to the programming language, such as integers, floating point values, or strings.
- Only discuss important data structures that are fully defined in the code given to you, not just imported or used.
- If there are relatively few important data structures, describe each of them.
- If there are many important data structures, focus on the most important data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a data structure.
"""

DATA_STRUCTURES_NONE_CONTENT = "No custom data structures."

FUNCTIONS_PROMPT = """
Summarize the functions or methods in the code provided below. For each function or method, describe the inputs, control flow and logic, and output.

- If there are no functions in the code, just say so and do not write anything else.
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
    ("## Data Structures", DATA_STRUCTURES_CHECKER, DATA_STRUCTURES_FOUND_PROMPT, lambda: DATA_STRUCTURES_NONE_CONTENT),
    ("## Functions", FUNCTIONS_PROMPT),
    # ("## Diagram", DIAGRAMS_PROMPT),
]
