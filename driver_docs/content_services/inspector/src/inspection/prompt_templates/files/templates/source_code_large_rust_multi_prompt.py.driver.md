# Purpose
This Python code is a configuration file that defines a template for analyzing and documenting Rust source code. It provides a structured approach to extract and describe various components of Rust code, such as imports, global variables, macros, traits, data structures, and functions. The file imports several utilities and classes from a `utils` module, which are used to perform static analysis and leverage language models (LLMs) to generate detailed documentation. The template is organized as a list of tuples, each specifying a section of the documentation, the method of analysis, and the expected output format. This code offers narrow functionality, specifically tailored for generating multi-context documentation for Rust codebases.
# Imports and Dependencies

---
- `utils.lang_specialization.default_multi_context`
- `utils.lang_specialization.rust`
- `utils.templates`


# Global Variables

---
### SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST 
- **Type**: `list`
- **Description**: `SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST` is a list of tuples, each containing a set of parameters used for generating prompts related to Rust source code analysis. Each tuple includes a prompt type, a section header, a system or user prompt, a function or method for processing, and an optional additional parameter. This structure is designed to facilitate the analysis and documentation of various components of Rust code, such as imports, global variables, macros, traits, data structures, and functions.
- **Use**: This variable is used to define a template for generating and processing prompts related to different aspects of Rust source code analysis.


