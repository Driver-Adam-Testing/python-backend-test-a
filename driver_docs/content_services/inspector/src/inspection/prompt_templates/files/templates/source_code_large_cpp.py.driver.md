# Purpose
This Python code defines a template for analyzing and documenting C++ source code, providing a structured approach to extract and describe various components of C++ files. It imports several specialized modules and classes from a utility library, which are used to identify and categorize elements such as global variables, data structures, and functions within C++ code. The `SOURCE_CODE_LARGE_TEMPLATE_CPP` is a list of tuples, each representing a section of the documentation, such as "Purpose," "Imports and Dependencies," "Global Variables," "Data Structures," and "Functions." Each section uses specific functions or classes to perform static analysis or leverage language models (LLMs) to generate detailed descriptions. This code offers narrow functionality, focusing specifically on the documentation of C++ code by leveraging Python's capabilities to automate and enhance the documentation process.
# Imports and Dependencies

---
- `utils.lang_specialization.cpp`
- `utils.lang_specialization.default`
- `utils.templates`


# Global Variables

---
### SOURCE_CODE_LARGE_TEMPLATE_CPP 
- **Type**: `list`
- **Description**: `SOURCE_CODE_LARGE_TEMPLATE_CPP` is a list of tuples, each containing a set of parameters used for processing and analyzing C++ source code. Each tuple includes a type of prompt or condition, a description header, and various functions or prompts related to C++ code analysis, such as system prompts, user prompts, and static analysis functions.
- **Use**: This variable is used to define a structured template for analyzing and processing large C++ source code files, organizing the analysis into sections like purpose, imports, global variables, data structures, and functions.


