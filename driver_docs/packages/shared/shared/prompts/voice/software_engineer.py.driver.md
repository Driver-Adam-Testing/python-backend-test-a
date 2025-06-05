# Purpose
This code defines a simple configuration setup for a system message in a software application. It consists of a multi-line string, `VOICE_PROMPT`, which outlines specific instructions or guidelines for a software engineer's role, and a dictionary, `MESSAGE`, which pairs a role identifier with the content of the `VOICE_PROMPT`. The functionality provided is narrow, focusing solely on defining a structured message format that could be used in a larger system, possibly for initializing or configuring a conversational AI or automated documentation tool. The code is straightforward and serves as a foundational component for setting up system messages or prompts.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary with two key-value pairs. The first key is 'role', which is associated with the string value 'system'. The second key is 'content', which is linked to the value of the `VOICE_PROMPT` variable, a multi-line string that describes the role and behavior of a software engineer.
- **Use**: This variable is used to store and convey a structured message, likely for use in a system that requires role-based content delivery.


---
### VOICE_PROMPT 
- **Type**: `str`
- **Description**: The `VOICE_PROMPT` variable is a multi-line string that serves as a predefined prompt or guideline for a software engineer's role. It outlines specific instructions and limitations, emphasizing the importance of writing code and documentation based on factual data without generalization or speculation.
- **Use**: This variable is used to set the content of the `MESSAGE` dictionary, providing context or instructions for a system role.


