# Purpose
This code defines a simple configuration setup for a system message in a software application, providing narrow functionality. It consists of two global variables: `PROMPT` and `MESSAGE`. The `PROMPT` variable contains a multi-line string that outlines the role of a technical document editor, specifying actions based on user requests. The `MESSAGE` variable is a dictionary with two keys, `role` and `content`, where `role` is set to "system" and `content` is assigned the value of the `PROMPT` string. This setup is likely used to configure or initialize a system message for a larger application, ensuring consistent behavior when handling user requests.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is assigned the string value 'system', and the 'content' key is assigned the value of the `PROMPT` variable, which is a multi-line string.
- **Use**: This variable is used to store system-level instructions or prompts, likely for use in a context where role-based messaging or command execution is required.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a multi-line message intended for a technical document editor. It provides instructions on how to handle user requests, specifically whether to execute tools for additional context or to modify language without context.
- **Use**: This variable is used to define the system's behavior in response to user requests, guiding the execution of tools or language modification.


