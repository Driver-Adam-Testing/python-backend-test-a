# Purpose
This code is a configuration setup for defining metadata templates, specifically for medium-sized systems, within a larger application. It imports specific constants and templates from utility modules, indicating that it is part of a broader system that likely deals with language processing or template generation. The `METADATA_MEDIUM_TEMPLATE` is a list containing tuples that define a structure for prompts, suggesting that this code is used to standardize or automate the generation of metadata prompts. The functionality provided is narrow, focusing on the configuration of metadata templates rather than performing any processing or computation itself. This setup is likely used in conjunction with other components to facilitate consistent metadata handling across the application.
# Imports and Dependencies

---
- `utils.lang_specialization.metadata`
- `utils.templates`


# Global Variables

---
### METADATA_MEDIUM_TEMPLATE 
- **Type**: `list`
- **Description**: `METADATA_MEDIUM_TEMPLATE` is a list containing a single tuple. This tuple consists of four elements: a string from `S.SINGLE_PROMPT_TEXT`, a string literal `"# Purpose"`, and two imported variables `METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT` and `PURPOSE_PROMPT_MEDIUM`. The list is likely used to define a template structure for metadata with medium complexity.
- **Use**: This variable is used to store a template configuration for medium-sized metadata prompts, combining text and imported prompt components.


