# Purpose
This Python code defines a template for analyzing and documenting source code, focusing on extracting and organizing key components such as imports, global variables, data structures, and functions. The file imports several utilities and classes from a module named `utils.lang_specialization.default`, which appear to be specialized for handling different aspects of source code analysis, such as collections of functions, variables, and data structures. Additionally, it imports a template utility `S` from `utils.templates`, which is used to define the structure of the documentation template.

The main component of this file is the `SOURCE_CODE_LARGE_TEMPLATE_DEFAULT`, a list of tuples that specify different sections of the documentation template. Each tuple includes a type of prompt or condition (e.g., `S.SINGLE_PROMPT_TEXT`, `S.LLM_COND_JSON`), a section header (e.g., "# Purpose", "# Imports and Dependencies"), and functions or methods that process and extract relevant information from the source code. This setup suggests that the file is part of a larger system designed to automate the generation of documentation for Python code, providing a structured approach to identify and describe the purpose, dependencies, and key elements of the codebase.
# Imports and Dependencies

---
- `utils.lang_specialization.default`
- `utils.templates`


# Global Variables

---
### SOURCE_CODE_LARGE_TEMPLATE_DEFAULT 
- **Type**: `list`
- **Description**: `SOURCE_CODE_LARGE_TEMPLATE_DEFAULT` is a list of tuples, each containing a set of parameters used for configuring different sections of a source code template. Each tuple includes a type identifier, a section title, and various functions or prompts related to that section.
- **Use**: This variable is used to define the structure and components of a large source code template, specifying how different sections like purpose, imports, global variables, data structures, and functions should be handled.


