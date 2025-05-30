# Purpose
This Python code defines a configuration for a multi-prompt template specifically tailored for analyzing C++ source code. It imports various utilities and classes from a module dedicated to language specialization, particularly for C++, and another module for handling multi-context prompts. The template, `SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP`, is a structured list of tuples, each representing a different aspect of C++ code analysis, such as purpose, imports, global variables, data structures, and functions. Each tuple specifies a type of prompt or condition, a description, and the methods or functions used to extract or analyze the relevant information from C++ code. This code provides narrow functionality, focusing on the detailed analysis and documentation of C++ source code components using a multi-prompt approach.
# Imports and Dependencies

---
- `utils.lang_specialization.cpp`
- `utils.lang_specialization.default_multi_context`
- `utils.templates`


# Global Variables

---
### SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP 
- **Type**: `list`
- **Description**: `SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP` is a list of tuples, each containing a set of parameters used to define prompts and conditions for analyzing C++ source code. These tuples include elements such as prompt types, section headers, and functions for static analysis and language model processing.
- **Use**: This variable is used to configure and manage the process of generating and handling prompts for analyzing and extracting information from C++ source code.


