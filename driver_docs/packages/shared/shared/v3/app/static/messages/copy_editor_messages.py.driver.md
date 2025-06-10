# Purpose
This Python code defines two classes, `CopyEditorSystemMessage` and `CopyEditorUserMessage`, which extend the `LlmMessage` class, likely used for handling messages in a language model interface. The `CopyEditorSystemMessage` class is a specialized message type with a predefined system message content that outlines detailed instructions for a technical copy editor, emphasizing clarity, conciseness, and relevance in document editing. The `CopyEditorUserMessage` class provides a method, `from_context`, to create user messages by wrapping and concatenating various document-related strings, such as text to edit and user prompts, into a single message content. This code provides narrow functionality, focusing specifically on structuring and managing messages for a copy editing system, and is part of a larger system that likely involves document processing and language model interactions.
# Imports and Dependencies

---
- `shared.v3.globals.glossary`
- `shared.v3.interfaces.llm_message`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that holds the complete message content for instances of the `CopyEditorSystemMessage` and `CopyEditorUserMessage` classes. In `CopyEditorSystemMessage`, it contains detailed instructions for a technical copy editor, while in `CopyEditorUserMessage`, it is constructed from various wrapped text components related to the editing context.
- **Use**: This variable is used to store and manage the message content for different types of messages in the copy editing system, ensuring that the appropriate instructions or context are conveyed.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is a global variable of type `MessageKind`, which is an enumeration imported from the `shared.v3.interfaces.llm_message` module. It is used to specify the kind of message being handled by the `CopyEditorSystemMessage` and `CopyEditorUserMessage` classes, with values such as `MessageKind.SYSTEM` and `MessageKind.USER`. This variable helps in categorizing messages within the system, allowing for appropriate handling and processing based on the message type.
- **Use**: The `message_kind` variable is used to define the type of message for instances of `CopyEditorSystemMessage` and `CopyEditorUserMessage`, indicating whether the message is a system or user message.


# Classes

---
### CopyEditorSystemMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
    - `content`: Contains detailed instructions and guidelines for editing technical documents.
- **Description**: The `CopyEditorSystemMessage` class is a specialized message class that inherits from `LlmMessage` and is designed to represent system-level instructions for a technical copy editor. It provides a comprehensive set of guidelines and instructions for editing technical documents, emphasizing clarity, conciseness, and relevance. The class sets the `message_kind` to `MessageKind.SYSTEM` and includes a detailed `content` string that outlines the expectations and tasks for the copy editor, such as removing redundant or speculative content, converting diagrams, and ensuring the document is useful and specific to the project.
- **Inherits From**:
    - LlmMessage


---
### CopyEditorUserMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.USER.
- **Description**: The `CopyEditorUserMessage` class is a specialized type of `LlmMessage` that represents a user message in the context of a copy editing task. It includes a class method `from_context` that constructs a `CopyEditorUserMessage` instance by wrapping and concatenating various pieces of text, such as the text to be edited, the original user prompt, and the content surrounding the cursor position in a document. This class is designed to encapsulate the user's input and context for processing by a copy editing system.
- **Inherits From**:
    - LlmMessage

**Methods**

---
#### CopyEditorUserMessage.from_context
The `from_context` function creates a `CopyEditorUserMessage` instance by wrapping and concatenating provided text segments.
- **Inputs**:
    - `text_to_edit`: A string representing the text that needs to be edited.
    - `original_user_prompt`: A string containing the original prompt given by the user.
    - `page_content_before_cursor`: A string representing the content of the page before the cursor position.
    - `page_content_after_cursor`: A string representing the content of the page after the cursor position.
- **Control Flow**:
    - The function takes four string arguments: `text_to_edit`, `original_user_prompt`, `page_content_before_cursor`, and `page_content_after_cursor`.
    - Each of these strings is wrapped using a corresponding wrapper function from imported modules: `TEXT_TO_EDIT.wrap`, `USER_PROMPT.wrap`, `DOCUMENT_CONTENT_BEFORE_CURSOR.wrap`, and `DOCUMENT_CONTENT_AFTER_CURSOR.wrap`.
    - The wrapped strings are concatenated together with newline characters separating them.
    - A new instance of `CopyEditorUserMessage` is created with the concatenated string as its content and returned.
- **Output**:
    - Returns an instance of `CopyEditorUserMessage` with the concatenated and wrapped content.



