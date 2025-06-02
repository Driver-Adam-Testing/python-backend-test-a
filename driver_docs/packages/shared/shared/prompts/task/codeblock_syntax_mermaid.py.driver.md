# Purpose
This code is a configuration script designed to guide a system, likely an AI or a software tool, in processing and correcting Mermaid.js code blocks within a document. It provides narrow functionality focused on ensuring that Mermaid diagrams are correctly formatted to avoid rendering errors. The script includes specific instructions to remove forbidden characters such as parentheses and double hyphens from element labels, correct syntax for lists within Mermaid blocks, and ensure that subgraph names do not contain spaces. Additionally, it emphasizes avoiding cycles in the diagram by not setting an element as a parent of itself. The code is structured as a prompt message, likely intended for use in a conversational AI or automated documentation tool, to ensure that Mermaid diagrams are accurately rendered and free of common formatting issues.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary containing two key-value pairs: 'role' and 'content'. The 'role' key is associated with the string 'system', indicating the context or type of message. The 'content' key holds a multi-line string stored in the variable `PROMPT`, which provides detailed instructions for reviewing and correcting mermaid code blocks.
- **Use**: This variable is used to store and convey system-level instructions for processing mermaid diagrams, ensuring they are correctly formatted and free of rendering errors.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a multi-line string that provides detailed instructions for reviewing and correcting mermaid code blocks in a document. It includes guidelines for avoiding rendering errors by removing forbidden characters and correcting syntax issues, such as ensuring proper list syntax and removing spaces in subgraph names.
- **Use**: This variable is used as a template or guideline for processing and correcting mermaid diagrams to ensure they render correctly without errors.


