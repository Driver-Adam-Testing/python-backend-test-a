# Purpose
This code is a configuration setup for a conversational AI or chatbot system, providing a specific prompt and message structure. It defines a `PROMPT` string that describes a scenario where the AI needs to generate content suitable for a fifth grader interested in computers and software. The `MESSAGE` dictionary uses this prompt to simulate a user input, while the `ASSISTANT_MESSAGE` dictionary outlines how the AI should respond, indicating that the response should be tailored to a young audience. This code offers narrow functionality, focusing on setting up a specific interaction scenario for educational purposes.
# Global Variables

---
### ASSISTANT_MESSAGE 
- **Type**: `dict`
- **Description**: The `ASSISTANT_MESSAGE` variable is a dictionary that represents a message from an assistant, with a specific role and content. The role is set to 'assistant', and the content is a string indicating the assistant's intention to respond in a manner suitable for a fifth grader.
- **Use**: This variable is used to define the assistant's response format and content in a conversation, particularly tailored for a young audience.


---
### MESSAGE 
- **Type**: `dict`
- **Description**: The `MESSAGE` variable is a dictionary that contains two key-value pairs: 'role' and 'content'. The 'role' key is assigned the value 'user', indicating the role of the entity associated with this message. The 'content' key is assigned the value of the `PROMPT` variable, which is a string containing a detailed description of the content to be curated for a fifth-grade audience.
- **Use**: This variable is used to store and represent a message from the user, including their role and the specific content they are interested in.


---
### PROMPT 
- **Type**: `str`
- **Description**: PROMPT is a string variable that contains a multi-line text prompt. This prompt is designed to guide the creation of content tailored for a fifth-grade audience, focusing on explaining computers and software in an engaging and simple manner.
- **Use**: This variable is used to store the instructional text that will be used to generate content for a specific reader persona.


