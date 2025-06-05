# Purpose
This code is a configuration file that defines a template for metadata generation, specifically for large systems. It imports specific prompt constants from a `utils.lang_specialization.metadata` module and a template structure from `utils.templates`. The `METADATA_LARGE_TEMPLATE` is a list of tuples, each containing a template type, a section header, and associated prompts for generating metadata related to the purpose and content summary of a system. This setup suggests a narrow functionality focused on structuring metadata prompts, likely used in a larger application for documentation or automated content generation.
# Imports and Dependencies

---
- `utils.lang_specialization.metadata`
- `utils.templates`


# Global Variables

---
### METADATA_LARGE_TEMPLATE 
- **Type**: `list`
- **Description**: `METADATA_LARGE_TEMPLATE` is a list of tuples, where each tuple contains four elements: a string from `S.SINGLE_PROMPT_TEXT`, a section header (e.g., '# Purpose'), a system prompt from `METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT`, and a specific prompt such as `PURPOSE_PROMPT_LARGE` or `CONTENT_SUMMARY_PROMPT`. This structure is used to define templates for metadata generation.
- **Use**: This variable is used to store and organize metadata templates for generating specific sections of content.


