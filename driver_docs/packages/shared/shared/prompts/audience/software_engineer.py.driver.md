# Purpose
This code defines a set of configuration variables and messages intended for a conversational AI or chatbot system. It includes a `PROMPT` string that outlines the expectations of a seasoned software engineer seeking detailed technical documentation, emphasizing the need for advanced topics, thorough examination, and relevant examples. The `MESSAGE` dictionary encapsulates this prompt, assigning it a "user" role, while the `ASSISTANT_MESSAGE` dictionary provides a structured response from the assistant, acknowledging the user's requirements and committing to delivering precise and contextually relevant information. This code provides narrow functionality, primarily serving as a template for initializing a conversation with specific expectations and responses in a chatbot or AI-driven documentation assistant.
# Global Variables

---
### ASSISTANT_MESSAGE 
- **Type**: `dict`
- **Description**: The `ASSISTANT_MESSAGE` is a dictionary that represents a message from an assistant, containing two key-value pairs: 'role' and 'content'. The 'role' key is set to 'assistant', indicating the source of the message, while the 'content' key contains a detailed string message outlining the assistant's understanding and approach to providing technical documentation.
- **Use**: This variable is used to store and convey the assistant's response message, which is tailored to provide in-depth technical information and analysis based on the user's inquiries.


---
### MESSAGE 
- **Type**: `dict`
- **Description**: The variable `MESSAGE` is a dictionary with two key-value pairs: 'role' and 'content'. The 'role' key is assigned the string value 'user', and the 'content' key is assigned the value of the `PROMPT` variable, which is a detailed string describing the expectations of a seasoned software engineer for technical documentation.
- **Use**: This variable is used to represent a user's request or input in a structured format, likely for communication with an assistant or AI model.


---
### PROMPT 
- **Type**: `str`
- **Description**: The variable `PROMPT` is a string that contains a detailed description of the expectations and requirements of a seasoned software engineer seeking in-depth technical documentation. It outlines the engineer's interest in advanced topics, technical enhancements, and specific codebase-related content, while explicitly stating a preference against generalized information.
- **Use**: This variable is used to define the content of a message that conveys the user's expectations and requirements for technical documentation.


