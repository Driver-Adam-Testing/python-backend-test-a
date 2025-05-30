# Purpose
This code defines a configuration for a language model prompt used in a technical copy editing context. It is a collection of string variables and a dictionary that outlines the specific instructions for editing technical documents. The `PROMPT` variable contains detailed guidelines for making technical documentation concise, specific, and free of unnecessary or redundant information. The `MESSAGE` dictionary encapsulates this prompt, associating it with a system role, likely for use in a larger application that processes or generates technical documentation. This code provides narrow functionality, focusing specifically on refining and improving the clarity and utility of technical documents.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary with two key-value pairs. The first key is 'role', which is assigned the string value 'system', and the second key is 'content', which is assigned the value of the `PROMPT` string.
- **Use**: This variable is used to store a structured message, likely for use in a system that processes or sends messages with specific roles and content.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a multi-line string that contains detailed instructions for a technical copy editor. It outlines the editor's role, emphasizing the importance of concise and specific technical writing, and provides guidelines for editing technical documents to enhance clarity and usefulness.
- **Use**: This variable is used to provide a comprehensive set of instructions for a technical copy editor to follow when editing a section of a technical document.


