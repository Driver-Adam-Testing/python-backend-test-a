# Purpose
This Python code defines a set of classes that facilitate the creation and management of messages for an inline editing system, specifically designed to interact with a language model. The primary purpose of this code is to structure and format messages that guide a language model in refining text based on user input. The code imports several constants and classes from shared modules, which are used to define the structure and content of these messages. The `InlineEditSystemMessage` and `InlineEditToolUseMessage` classes are designed to provide system-level instructions to the language model, detailing how it should interpret and respond to user prompts and how to handle situations where additional context is needed. The `InlineEditUserMessage` class, on the other hand, is responsible for constructing user-specific messages by wrapping user prompts and document content in predefined XML-like tags, ensuring that the language model can accurately identify and process the relevant sections of text.

The code is structured as a library file intended to be imported and used within a larger application that manages document editing through a language model interface. It defines a public API for creating and managing different types of messages, which are essential for the inline editing process. The use of class methods and structured message content ensures that the language model receives clear and consistent instructions, enabling it to perform precise text modifications based on user input. This code provides a narrow but crucial functionality within the context of a document editing system, focusing on the interaction between user prompts, document content, and the language model's response.
# Imports and Dependencies

---
- `shared.v3.globals.glossary`
- `shared.v3.interfaces.llm_message.LlmMessage`
- `shared.v3.interfaces.llm_message.MessageKind`


# Global Variables

---
### content 
- **Type**: ``str``
- **Description**: The `content` variable is a string attribute of the `InlineEditSystemMessage`, `InlineEditToolUseMessage`, and `InlineEditUserMessage` classes, which are subclasses of `LlmMessage`. It contains predefined text that describes the role and instructions for a technical writer or the actions to be taken based on user prompts and document context.
- **Use**: This variable is used to store and convey specific instructions or messages related to inline editing tasks, which are then utilized by the system to guide the editing process.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is a global variable defined in the `InlineEditSystemMessage`, `InlineEditToolUseMessage`, and `InlineEditUserMessage` classes. It is of type `MessageKind`, which is likely an enumeration or class that categorizes different types of messages in the system.
- **Use**: This variable is used to specify the kind of message being handled, such as 'SYSTEM' or 'USER', to differentiate between system-generated messages and user-generated messages.


# Classes

---
### InlineEditSystemMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
    - `content`: Contains a detailed string describing the role and instructions for a technical writer in an inline edit system.
- **Description**: The `InlineEditSystemMessage` class is a specialized message class that inherits from `LlmMessage` and is used to define system-level instructions for a technical writer in an inline editing context. It sets the `message_kind` to `MessageKind.SYSTEM` and provides a detailed `content` string that outlines the writer's task of refining text based on user prompts, specifically focusing on replacing only the selected text segment in a document. The class utilizes several constants to mark different parts of the document and user prompt, ensuring precise and context-aware text editing.
- **Inherits From**:
    - LlmMessage


---
### InlineEditToolUseMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
    - `content`: Contains a string instructing the use of tools to obtain context from source code or documentation when user prompts lack explicit information.
- **Description**: The `InlineEditToolUseMessage` class is a specialized message type that inherits from `LlmMessage`. It is designed to handle scenarios where a user prompt requires additional context not present in the document. The class sets the message kind to `SYSTEM` and provides a specific instruction in its content to use tools for gathering necessary context from source code or documentation.
- **Inherits From**:
    - LlmMessage


---
### InlineEditUserMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.USER.
- **Description**: The `InlineEditUserMessage` class is a specialized type of `LlmMessage` designed to encapsulate user messages in an inline editing context. It includes a class method `from_context` that constructs an instance of `InlineEditUserMessage` by wrapping the user prompt and document content around the cursor position, effectively formatting the message content for processing. This class is part of a system that handles user interactions for inline text editing, where the user specifies a prompt and selects text within a document for modification.
- **Inherits From**:
    - LlmMessage

**Methods**

---
#### InlineEditUserMessage.from_context
The `from_context` function creates an `InlineEditUserMessage` object by wrapping and concatenating user prompt and document content around the cursor position.
- **Inputs**:
    - `cls`: The class reference to `InlineEditUserMessage`, used to create an instance of this class.
    - `user_prompt`: A string containing the user's prompt or instructions for editing the document.
    - `page_content_before_cursor`: A string representing the content of the document before the cursor position.
    - `selected_text`: A string representing the text selected by the user, which is intended to be edited.
    - `page_content_after_cursor`: A string representing the content of the document after the cursor position.
- **Control Flow**:
    - The function is a class method, indicated by the `cls` parameter, which is used to create an instance of `InlineEditUserMessage`.
    - The function constructs a string by wrapping the `user_prompt` with `USER_PROMPT.wrap`.
    - It concatenates the wrapped `page_content_before_cursor`, `selected_text`, and `page_content_after_cursor` using their respective wrappers: `DOCUMENT_CONTENT_BEFORE_CURSOR.wrap`, `CURSOR.wrap`, `CURSOR_SELECTION.wrap`, and `DOCUMENT_CONTENT_AFTER_CURSOR.wrap`.
    - The concatenated and wrapped content is further wrapped with `WORKING_DOCUMENT_CONTENT.wrap`.
    - The final wrapped content is passed as the `content` argument to the `InlineEditUserMessage` constructor, and the resulting object is returned.
- **Output**:
    - An instance of `InlineEditUserMessage` with its `content` attribute set to the wrapped and concatenated string of user prompt and document content.



