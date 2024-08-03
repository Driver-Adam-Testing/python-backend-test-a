from pathlib import Path
from typing import Optional
from utils.codemap_ctags import extract_symbols_w_ctags
from utils.templates import S
import logging
from utils.lang_specialization.cpp import cpp_data_structure_checker, cpp_function_checker, cpp_variables_checker, cpp_namespace_checker


SOURCE_CODE_SMALL_SYSTEM_PROMPT_CPP = """
You are an expert C++ programmer and a software engineering documentation expert. You write detailed documentation to explain code written in C++.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.

You specialize in effectively describing small and short source code files. Your goal is to be terse and clear, since the source code you are describing is small and simple.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Consider questions such as the following when providing your output:

- Does this code provide narrow or broad functionality?
- What kind of code is this? For example, is this code a short script, a simple C header file, a collection of global variables or configuration variables, etc.?
"""

NAMESPACES_FOUND_PROMPT = """
Summarize the namespaces in the code provided below.

- Summarize the content inside the namespace.
- When describing a namespace, provide detail that matches the complexity of the namespace. Large namespaces with many large components should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a 1 to 3 sentence description of the namespace.
"""

DATA_STRUCTURES_FOUND_PROMPT = """
Summarize the important data structures in the code provided below.

- A data structure is custom or compound type in a given programming language, such as structs, classes, or enums. Functions, methods, and variables are not data structures.
- Only discuss custom, complex, or compound data structures defined in the code below. Do not talk about the most primitive types inherent to C++, such as integers, floating point values, or strings.
- Only describe important data structures **fully defined** in the code given to you. That is, the implementation of the data structure is in the source code given to you. If a data structure is imported or used without being defined in the code, do not describe it.
- If there are relatively few important data structures, describe each of them.
- If there are many important data structures, focus on the most important data structures.
- When describing an important data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a data structure.
"""

FUNCTIONS_FOUND_PROMPT = """
Summarize the functions or methods in the code provided below. For each function or method, describe the inputs, control flow and logic, and output.

- If there are no functions in the code, just say so and do not write anything else.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important functions or methods.
- If you are describing a method of a class rather than a free function, identify the class the method is associated with when you describe it.
- When describing a function or method, provide detail that matches the complexity of the function or method body. Large and complex functions or methods should get longer explanations, while small ones much less.
- Provide your output such that each function or method is described in a 3rd level markdown header where the function or method name is the header title (e.g., ### <function_name>).
"""

MACROS_FOUND_PROMPT = """
Summarize the macros or methods in the code provided below.

- If there are relatively few macros, describe each of them.
- If there are many macros, focus on the most important ones.
- If you are describing a method of a class rather than a free function, identify the class the method is associated with when you describe it.
- When describing a macro, provide detail that matches the complexity of the macro body. Large and complex macros should get longer explanations, while small ones much less.
- Provide your output in a list, where each item of the list is a macro.
"""


VARIABLES_FOUND_PROMPT = """
Summarize the global variables in the code provided below.

- A global variable is declared at the top level scope. Local variables declared and used inside of functions are not global variables.
- Only describe global variables.
- If there are many global variables, focus on the most important ones.
- When describing a global variable, provide detail that matches the complexity of the variable. Large and complex global variables (e.g., containing large struct instances) should get longer explanations, while small ones (e.g., one line definitions) much less.
- Provide your output in a list, where each item of the list is a global variable.
"""


SOURCE_CODE_SMALL_TEMPLATE_CPP = [
    (S.RAW, "# Overview",),
    (S.SINGLE_PROMPT, "## Purpose", PURPOSE_PROMPT),
    # (S.FN_COND,       "## Macros", c_macro_checker, MACROS_FOUND_PROMPT, None),
    # (S.FN_COND,       "## Namespaces", cpp_namespace_checker, NAMESPACES_FOUND_PROMPT, None),
    (S.FN_COND,       "## Global Variables", cpp_variables_checker, VARIABLES_FOUND_PROMPT, None),
    (S.FN_COND,       "## Data Structures", cpp_data_structure_checker, DATA_STRUCTURES_FOUND_PROMPT, None),
    (S.FN_COND,       "## Functions", cpp_function_checker, FUNCTIONS_FOUND_PROMPT, None),
]
