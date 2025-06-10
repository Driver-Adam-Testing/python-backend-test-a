# Purpose
This code defines a set of string constants that serve as prompts for generating documentation and summaries related to metadata or configuration files within a software codebase. The prompts are categorized based on the size and complexity of the files they describe, such as small, medium, and large, and are intended to guide the generation of detailed explanations or summaries. The functionality provided by this code is narrow, focusing specifically on the creation of documentation for non-code files, emphasizing clarity and conciseness. These prompts are likely used in a system that automates or assists in the documentation process, ensuring that the generated content is consistent and informative.
# Global Variables

---
### CONTENT_SUMMARY_FROM_CHUNKS 
- **Type**: `str`
- **Description**: The variable `CONTENT_SUMMARY_FROM_CHUNKS` is a string that contains a multi-line prompt. This prompt is designed to guide the user in combining multiple technical summary paragraphs into a cohesive summary that describes the technical content of an entire file. It emphasizes the need for a comprehensive and coherent summary of overlapping chunks of metadata or configuration file content.
- **Use**: This variable is used as a prompt to instruct users on how to create a unified content summary from multiple overlapping technical summaries.


---
### CONTENT_SUMMARY_PROMPT 
- **Type**: `str`
- **Description**: CONTENT_SUMMARY_PROMPT is a string variable that contains a multi-line prompt designed to guide the summarization of metadata or configuration file contents. It instructs the user to summarize the functional details of a file's contents, with an emphasis on adjusting the summary length based on the complexity and length of the content.
- **Use**: This variable is used to provide a template or guideline for generating detailed content summaries of metadata or configuration files in a software codebase.


---
### METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT 
- **Type**: `string`
- **Description**: The `METADATA_MEDIUM_AND_LARGE_SYSTEM_PROMPT` is a string variable that contains a detailed prompt for a software engineering documentation expert. It outlines the expert's role in explaining software, particularly focusing on configuration and metadata files. The prompt emphasizes the importance of confident and accurate documentation without speculation.
- **Use**: This variable is used to provide a detailed prompt for generating documentation related to medium and large configuration and metadata files.


---
### METADATA_SMALL_SYSTEM_PROMPT 
- **Type**: `str`
- **Description**: `METADATA_SMALL_SYSTEM_PROMPT` is a string variable that contains a prompt designed for a software engineering documentation expert. It emphasizes the expert's ability to write detailed documentation, particularly for small configuration and metadata files such as markdown, JSON, YAML, and Makefiles. The prompt instructs the expert to avoid speculation and to write with confidence.
- **Use**: This variable is used to provide a predefined prompt for generating documentation related to small configuration and metadata files.


---
### PURPOSE_FROM_CHUNKS 
- **Type**: `str`
- **Description**: `PURPOSE_FROM_CHUNKS` is a string variable that contains a multi-line prompt. This prompt is designed to guide the user in combining multiple purpose paragraphs into a single cohesive paragraph that describes the purpose of an entire file. It is part of a system that processes metadata or configuration files.
- **Use**: This variable is used to provide a template for generating a unified purpose description from multiple overlapping purpose paragraphs.


---
### PURPOSE_PROMPT_LARGE 
- **Type**: `string`
- **Description**: `PURPOSE_PROMPT_LARGE` is a string variable that contains a multi-line prompt designed to guide the explanation of the purpose of metadata or configuration files within a software codebase. The prompt encourages a detailed analysis of the file's purpose, including its type, functionality, conceptual components, and relevance to the codebase.
- **Use**: This variable is used to provide a structured guideline for generating comprehensive explanations of the purpose of large metadata or configuration files.


---
### PURPOSE_PROMPT_MEDIUM 
- **Type**: `string`
- **Description**: `PURPOSE_PROMPT_MEDIUM` is a string variable that contains a template for generating a prompt. This prompt is designed to guide the user in explaining the purpose of a metadata or configuration file from a software codebase in a concise manner. The prompt instructs the user to provide a single paragraph explanation, focusing on the purpose of the file contents.
- **Use**: This variable is used to generate a prompt that helps users articulate the purpose of medium-sized metadata or configuration files.


---
### PURPOSE_PROMPT_SMALL 
- **Type**: `str`
- **Description**: `PURPOSE_PROMPT_SMALL` is a string variable that contains a template for generating a concise explanation of the purpose of small metadata or configuration files within a software codebase. The template instructs the user to provide a brief, 1 to 3 sentence paragraph that explains the file's purpose without speculation.
- **Use**: This variable is used to guide the creation of succinct purpose descriptions for small files in a software documentation context.


