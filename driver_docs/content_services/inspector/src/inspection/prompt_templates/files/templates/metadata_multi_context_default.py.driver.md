# Purpose
This Python code defines a configuration for metadata templates, specifically for handling multi-context scenarios. It imports specific constants and templates from utility modules, indicating that it is part of a larger system focused on language specialization and template management. The `METADATA_MULTI_CONTEXT_TEMPLATE` is a list of tuples, each representing a structured template configuration for different purposes, such as "Purpose" and "Content Summary." Each tuple includes a prompt text, a section header, and several constants that likely guide the generation or processing of metadata. This code provides narrow functionality, serving as a configuration or setup file within a broader application, rather than performing any direct computation or logic processing itself.
# Imports and Dependencies

---
- `utils.lang_specialization.metadata`
- `utils.templates`


# Global Variables

---
### METADATA_MULTI_CONTEXT_TEMPLATE 
- **Type**: `list`
- **Description**: `METADATA_MULTI_CONTEXT_TEMPLATE` is a list of tuples, where each tuple contains elements related to metadata prompts and their associated processing functions. Each tuple includes a prompt type, a section header, a system prompt, a specific prompt, and a function to derive information from chunks.
- **Use**: This variable is used to define templates for generating metadata in different contexts, such as purpose and content summary, by associating prompts with their processing functions.


