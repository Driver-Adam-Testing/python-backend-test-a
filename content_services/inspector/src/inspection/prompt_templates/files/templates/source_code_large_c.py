from pathlib import Path
from typing import Optional
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.templates import S
from utils.c_specialization import c_data_structure_checker, c_function_checker, c_macro_checker, c_variables_checker
import logging


SOURCE_CODE_LARGE_SYSTEM_PROMPT_C = """
You are an expert C programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- Is this code a collection of many different components? If so, what is the common theme or purpose?
- What kind of code is this? For example, is this code clearly an executable (e.g., main.c), a C header file, a C file or library intended to be imported elsewhere?
- Does it define public APIs or external interfaces?
"""

TECHNICAL_SUMMARY_PROMPT = """
In one or more paragraphs, summarize the important technical concepts of the code provided below. Choose a summary length appropriate for the length and complexity of code. Longer and more complex code should have more summary content.

In writing your technical summary, write about about the conceptual use cases, applications, logic, and component interactions in the code instead of focusing on particular functions, variables, etc. A new developer can read your output and conceptually understand the core technical elements of the code before diving into source code.
"""

IMPORTS_PROMPT = """
Summarize the header files and imports used in the code provided below.

- If there are no header files or imports, just say so and do not write anything else.
- If it is completely clear what a header file or import is for, briefly describe it. Do not speculate -- if it is not completely clear what a header file provides just identify it without attempting to describe it.
"""

DATA_STRUCTURES_CHECKER = """
Your job is to determine if there are any important data structures defined in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- An important data structure is a custom, complex, or compound data structure in the language of the provided code but does not include primitive types inherent to the programming language such as integers, floating point values, or strings.
- You are only looking for important data structures that are **fully defined** in the code given to you. That is, the implementation of the data structure is in the source code given to you. If a data structure is imported or used without being defined in the code, it is not to be considered.

**You only respond with the text 'true' or 'false'.**
- If there is one or more data structure, as described above, respond with 'true'.
- Otherwise, respond with 'false'.
"""

DATA_STRUCTURES_FOUND_PROMPT = """
Summarize the important data structures in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- Only discuss custom, complex, or compound data structures defined in the code below. Do not talk about the most primitive types inherent to the programming language, such as integers, floating point values, or strings.
- Only describe important data structures **fully defined** in the code given to you. That is, the implementation of the data structure is in the source code given to you. If a data structure is imported or used without being defined in the code, do not describe it.
- If there are relatively few important data structures, describe each of them.
- If there are many important data structures, focus on the most important data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a data structure.
"""

DATA_STRUCTURES_NONE_CONTENT = "No custom data structures defined in this file."

FUNCTIONS_FOUND_PROMPT = """
Summarize the functions or methods in the code provided below. For each function or method, describe the inputs, control flow and logic, and output.

- If there are no functions in the code, just say so and do not write anything else.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important functions or methods.
- If you are describing a method of a class rather than a free function, identify the class the method is associated with when you describe it.
- When describing a function or method, provide detail that matches the complexity of the function or method body. Large and complex functions or methods should get longer explanations, while small ones much less.
- Provide your output such that each function or method is described in a 3rd level markdown header where the function or method name is the header title (e.g., ### <function_name>).
"""

FUNCTIONS_NONE_CONTENT = "No functions or function prototypes defined in this file."


MACROS_FOUND_PROMPT = """
Summarize the macros or methods in the code provided below.

- If there are relatively few macros, describe each of them.
- If there are many macros, focus on the most important ones.
- If you are describing a method of a class rather than a free function, identify the class the method is associated with when you describe it.
- When describing a macro, provide detail that matches the complexity of the macro body. Large and complex macros should get longer explanations, while small ones much less.
- Provide your output in a list, where each item of the list is a marco.
"""


VARIABLES_FOUND_PROMPT = """
Summarize the global variables in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables.
- Only describe global variables.
- If there are many global variables, focus on the most important ones.
- When describing a global variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
- Provide your output in a list, where each item of the list is a global variable.
"""


SOURCE_CODE_LARGE_TEMPLATE_C = [
    (S.RAW,           "# Overview"),
    (S.SINGLE_PROMPT, "## Purpose", PURPOSE_PROMPT),
    (S.SINGLE_PROMPT, "## Technical Summary", TECHNICAL_SUMMARY_PROMPT),
    (S.SINGLE_PROMPT, "## Imports and Dependencies", IMPORTS_PROMPT),
    # (S.FN_COND,       "## Macros", c_macro_checker, MACROS_FOUND_PROMPT, None),
    (S.FN_COND,       "## Global Variables", c_variables_checker, VARIABLES_FOUND_PROMPT, None),
    (S.FN_COND,       "## Data Structures", c_data_structure_checker, DATA_STRUCTURES_FOUND_PROMPT, lambda: DATA_STRUCTURES_NONE_CONTENT),
    (S.FN_COND,       "## Functions", c_function_checker, FUNCTIONS_FOUND_PROMPT, lambda: FUNCTIONS_NONE_CONTENT),
]
