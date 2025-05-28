# Purpose
This code defines a configuration for a system message in a structured format, likely intended for use in a chatbot or automated response system. It consists of a single global variable, `PROMPT`, which contains a multi-line string that outlines the guidelines for generating responses based on technical context. The `MESSAGE` dictionary uses this `PROMPT` as its content, associating it with a "system" role, suggesting that it is part of a larger framework where different roles (e.g., user, assistant) are defined. The functionality provided is narrow, focusing specifically on setting up a predefined system message template.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary that contains two key-value pairs: 'role' and 'content'. The 'role' key is associated with the string value 'system', and the 'content' key is associated with the value of the `PROMPT` variable, which is a multi-line string.
- **Use**: This variable is used to store a structured message format, likely for communication or configuration purposes within a system.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a detailed instruction set for a system or AI to follow when generating responses. It emphasizes understanding technical context and providing responses based on available documentation and source code.
- **Use**: This variable is used to guide the behavior of a system or AI in generating contextually relevant and accurate responses.


