# Purpose
This code defines a specialized message class, `SoftwareExpertiseMessage`, which extends the `LlmMessage` class from an imported module. The purpose of this class is to encapsulate a specific type of message, characterized by its `message_kind` attribute set to `MessageKind.SYSTEM`, indicating it is a system-level message. The `content` attribute provides a detailed description of the role and responsibilities of an expert software engineer, emphasizing the focus on writing high-quality code and documentation while avoiding instructing others or making unsupported generalizations. This code provides narrow functionality, specifically for creating a predefined message type within a larger system that likely involves message handling or communication protocols.
# Imports and Dependencies

---
- `shared.v3.interfaces.llm_message.LlmMessage`
- `shared.v3.interfaces.llm_message.MessageKind`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that provides a detailed description of the role and responsibilities of an expert software engineer. It outlines the expertise in software development, engineering, embedded systems, and technical writing, emphasizing the focus on writing high-quality code and documentation without instructing others.
- **Use**: This variable is used to define the default content of a `SoftwareExpertiseMessage`, setting the context and expectations for the message's purpose and scope.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is a class attribute of the `SoftwareExpertiseMessage` class, which is a subclass of `LlmMessage`. It is assigned the value `MessageKind.SYSTEM`, indicating the type of message this class represents within the system.
- **Use**: This variable is used to categorize the message as a system-level message within the context of the `SoftwareExpertiseMessage` class.


# Classes

---
### SoftwareExpertiseMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
    - `content`: Contains a detailed description of the software engineer's expertise and responsibilities.
- **Description**: The SoftwareExpertiseMessage class is a specialized message type that inherits from LlmMessage, designed to convey the expertise and responsibilities of a software engineer. It sets the message kind to SYSTEM and provides a detailed content string that outlines the engineer's extensive knowledge in software development, engineering, embedded systems, and technical writing. The message emphasizes the engineer's role in producing high-quality code and documentation, while explicitly stating that they should not instruct others or make unsupported generalizations.
- **Inherits From**:
    - LlmMessage


