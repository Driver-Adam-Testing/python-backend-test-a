# Purpose
This code defines a class `GlobalSystemMessage` that extends `LlmMessage` and serves as a global system message within an LLM (Large Language Model) framework. The purpose of this class is to establish universal behaviors and guidelines for handling LLM calls, ensuring consistency across different API, model, and pipeline interactions. It specifies that inputs will include XML tags for request components, tool calls must be formatted as JSON, and final responses should be in markdown without XML tags. The class encapsulates narrow functionality, focusing on defining and enforcing message handling rules within the LLM framework, and it includes a detailed docstring and a `content` attribute that outlines the expected behavior and response format for the assistant.
# Imports and Dependencies

---
- `shared.v3.interfaces.llm_message.LlmMessage`
- `shared.v3.interfaces.llm_message.MessageKind`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that contains a predefined message for the GlobalSystemMessage class, which is part of the LLM Framework. This message outlines the expected behavior of the assistant, including how it should respond to requests using tool calls or final responses, and the formats these responses should take.
- **Use**: This variable is used to define the default message content for instances of the GlobalSystemMessage class, guiding the assistant's response behavior.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is an instance of the `MessageKind` enumeration, specifically set to `MessageKind.SYSTEM`. It is used within the `GlobalSystemMessage` class, which is a subclass of `LlmMessage`. This class represents a global system message for the LLM Framework, defining universal behaviors for LLM calls.
- **Use**: This variable is used to specify the type of message being handled by the `GlobalSystemMessage` class, indicating that it is a system-level message.


# Classes

---
### GlobalSystemMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
    - `content`: Contains the instructions and guidelines for the assistant's responses.
- **Description**: The GlobalSystemMessage class is a specialized message class within the LLM Framework that defines universal behaviors for all LLM calls. It ensures that the system message remains agnostic of the specific API, model, or pipeline being used. The class outlines the expected input format, such as XML tags for request components, and specifies that tool calls must be formatted as JSON. It also defines universal glossary terms, ensuring that the final assistant response is always in markdown format without XML tags, unless explicitly requested by the user.
- **Inherits From**:
    - LlmMessage


