# Purpose
This code defines a couple of global variables, `PROMPT` and `MESSAGE`, which are likely used for configuring or setting up a system's messaging or instruction framework. The `PROMPT` variable contains a multi-line string that provides a detailed description of how a "smart_instruction" should be executed within a document, emphasizing the importance of focusing solely on the prompt section. The `MESSAGE` variable is a dictionary that assigns the role of "system" to the content of `PROMPT`, suggesting that it is used in a context where roles and content are structured, possibly in a chatbot or automated document processing system. This code provides narrow functionality, primarily serving as a configuration or setup for a larger system that processes or generates text based on specific instructions.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary that contains two key-value pairs: 'role' and 'content'. The 'role' key is assigned the value 'system', indicating the type or context of the message. The 'content' key is assigned the value of the `PROMPT` variable, which is a multi-line string providing instructions or context for a document.
- **Use**: This variable is used to encapsulate and structure a message with a specific role and content, likely for use in a system that processes or generates text based on the provided instructions.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a detailed instruction set, referred to as 'smart_instruction', which provides context and guidelines for executing a specific task within a document. It emphasizes focusing solely on the prompt section while other parts of the document serve as placeholders for additional instructions.
- **Use**: This variable is used to define the instructions and context for processing a document, ensuring that the focus remains on executing the specified prompt.


