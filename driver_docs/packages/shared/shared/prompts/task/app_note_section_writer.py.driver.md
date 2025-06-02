# Purpose
This code defines a couple of global variables, `PROMPT` and `MESSAGE`, which are likely used in a broader application context to facilitate the generation of technical documentation. The `PROMPT` variable contains a multi-line string that outlines a task for writing a detailed technical document, emphasizing the need for thorough understanding and context retrieval before drafting the document in markdown format. The `MESSAGE` variable is a dictionary with a "role" key set to "system" and a "content" key that holds the `PROMPT` string, suggesting its use in a system that processes or generates messages, possibly in a conversational AI or documentation generation tool. This code provides narrow functionality, primarily serving as a configuration or setup for a larger system that automates or assists in technical writing tasks.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is associated with the string 'system', and the 'content' key is associated with the string stored in the `PROMPT` variable. This dictionary is likely used to define a message structure for a system role in a communication or messaging context.
- **Use**: This variable is used to store and represent a structured message with a specific role and content, likely for use in a messaging or communication system.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a multi-line string that contains detailed instructions for writing a section of a technical document called an app note. It emphasizes the need for in-depth insights and understanding of the codebase related to the technical concept before writing the document.
- **Use**: This variable is used to provide a template or guideline for generating technical documentation, ensuring that the writer conducts thorough research and analysis before finalizing the document.


