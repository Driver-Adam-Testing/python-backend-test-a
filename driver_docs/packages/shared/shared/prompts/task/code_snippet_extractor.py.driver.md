# Purpose
This code defines a configuration for a system message in a software application, specifically for a role-based messaging system. It consists of two global variables: `PROMPT`, a multi-line string that provides instructions for a software engineer to identify and extract code examples from a document, and `MESSAGE`, a dictionary that pairs a role identifier with the content of the `PROMPT`. The functionality is narrow, focusing on setting up a specific message format for a system role, likely used in a larger application to guide user interactions or automate tasks related to code extraction. This code is a simple configuration setup rather than a functional script or module.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary with two key-value pairs. The first key is 'role' with the value 'system', and the second key is 'content' with the value of the string stored in the `PROMPT` variable.
- **Use**: This variable is used to store a structured message, likely for use in a system that requires role-based communication or configuration.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a multi-line message. This message provides instructions for a software engineer to identify and extract various types of code examples from a document. It specifies the types of code to look for, such as CLI commands, code examples, source code, and code snippets.
- **Use**: This variable is used to store the instructions that are likely utilized in a system message or prompt to guide a software engineer in identifying code examples.


