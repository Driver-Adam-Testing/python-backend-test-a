# Purpose
This code defines a simple configuration for a messaging system, specifically setting up a system message with a predefined prompt. It consists of a string variable `PROMPT` that contains a message template, and a dictionary `MESSAGE` that uses this prompt as its content, with the key "role" set to "system". The functionality provided is narrow, as it primarily serves to initialize a specific message format that can be used in a larger application, likely one that involves communication or interaction with users. This setup suggests that the code is part of a larger system where messages are structured and roles are defined, possibly for a chatbot or an automated response system.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is assigned the string 'system', and the 'content' key is assigned the value of the `PROMPT` variable, which is a string containing instructions for tool calls.
- **Use**: This variable is used to store and convey system-level instructions or messages, likely for communication or configuration purposes in a larger application.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a detailed instruction or guideline for a system process. It describes the necessity of including a thought with every batch of tool calls, explaining the thought to the user, and ensuring it is accompanied by other tools.
- **Use**: This variable is used to provide a consistent and clear instruction for how thoughts should be communicated to the user in the context of tool calls.


