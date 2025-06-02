# Purpose
This Python code defines a structured template for analyzing and documenting the components of a Python source code file. It imports several modules and classes from a utility library, which are used to facilitate the extraction and organization of information about the source code's purpose, imports, global variables, classes, and functions. The code is organized as a list of tuples, each representing a different aspect of the source code to be documented. Each tuple contains a specific template type, a section header, and a combination of static analysis and language model-based methods to extract and format the relevant information.

The primary purpose of this code is to provide a systematic approach to generating documentation for Python source files by breaking down the file into its constituent parts and analyzing each part using both static analysis and machine learning techniques. This code is likely part of a larger documentation generation system, where it serves as a template to ensure consistent and comprehensive documentation output. The use of collections like `PyClassCollection` and `PyFnCollection` suggests that the code is designed to handle complex source files with multiple classes and functions, making it suitable for broad functionality in documenting Python projects.
# Imports and Dependencies

---
- `utils.lang_specialization.default_multi_context`
- `utils.lang_specialization.python`
- `utils.templates`


# Global Variables

---
### SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_PY 
- **Type**: `list`
- **Description**: `SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_PY` is a list of tuples, where each tuple represents a different section of a multi-prompt template used for analyzing Python source code. Each tuple contains elements that define the type of prompt, a section header, and various functions or constants that are used to process or analyze that section of the code.
- **Use**: This variable is used to structure and organize the process of generating prompts for analyzing different aspects of Python source code, such as purpose, imports, global variables, classes, and functions.


