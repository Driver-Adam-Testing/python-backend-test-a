# Purpose
This code defines a configuration for a messaging system, specifically setting up a system message with a predefined prompt. The `PROMPT` variable contains a detailed instruction set, likely intended for an automated system or AI to follow when executing tasks, emphasizing the use of multiple tools and cautioning against certain actions. The `MESSAGE` dictionary encapsulates this prompt with a role designation, suggesting its use in a context where messages are exchanged, such as a chatbot or automated assistant. The functionality provided is narrow, focusing on setting up a specific message format rather than implementing broader logic or operations.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is assigned the value 'system', indicating the type or context of the message. The 'content' key is assigned the value of the `PROMPT` variable, which contains a string of instructions or guidelines for executing tools and handling responses.
- **Use**: This variable is used to store and convey system-level instructions or guidelines for executing tools and managing responses in a structured format.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a detailed instruction set for executing multiple tools in iterations, emphasizing the importance of using a diverse set of tools and searching descriptions at least once. It also includes strict guidelines against inventing or using undefined functions and specifically prohibits invoking the `multi_tool_use.parallel` function.
- **Use**: This variable is used to store a set of instructions or guidelines, likely for a system or process that involves tool execution and context gathering.


