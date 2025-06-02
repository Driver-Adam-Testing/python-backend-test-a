# Purpose
This code defines a configuration for a prompt engineering system, specifically tailored for enhancing user prompts to improve interactions with a language model (LLM). It consists of a single string variable, `PROMPT`, which contains detailed instructions for generating concise and effective prompts. The instructions emphasize brevity, clarity, and adherence to user specifications regarding the desired length and format of the LLM's output. Additionally, a dictionary `MESSAGE` is created, associating the role of "system" with the `PROMPT` content, likely for use in a conversational AI context. This code provides narrow functionality, focusing on prompt enhancement for technical documentation tasks.
# Global Variables

---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary with two key-value pairs. The first key is 'role', which has the value 'system', and the second key is 'content', which holds the value of the `PROMPT` string. This dictionary is likely used to configure or define a system message or instruction for a language model or similar system.
- **Use**: This variable is used to store and pass a system role and its associated prompt content to a language model or similar system for processing.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a multi-line string that serves as a detailed instruction set for a prompt engineer. It outlines the expected behavior and response format when interacting with a language model, emphasizing brevity and clarity in responses.
- **Use**: This variable is used to guide the language model in generating enhanced prompts for technical documentation tasks.


