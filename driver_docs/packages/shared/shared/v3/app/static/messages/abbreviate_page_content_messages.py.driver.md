# Purpose
This Python code defines two classes, `AbbreviatePageContentSystemMessage` and `AbbreviatePageContentUserMessage`, which are specialized message types inheriting from the `LlmMessage` class. These classes are part of a system designed to preprocess and structure document content for use by a downstream language model (LLM). The primary purpose of this code is to facilitate the conversion of document sections into concise, information-dense summaries that can be effectively utilized by an LLM to generate accurate and non-redundant technical documentation or explanations. The `AbbreviatePageContentSystemMessage` class provides a detailed system message that outlines the objectives and guidelines for processing document content, ensuring that the LLM has the necessary context to avoid unnecessary external searches and to accurately interpret the document's content. The `AbbreviatePageContentUserMessage` class, on the other hand, is designed to create user messages based on a given prompt and document content, focusing on summarizing relevant parts of the document in relation to the user's query.

The code imports several constants and classes from shared modules, indicating that it is part of a larger system or library. The use of constants like `IMPORTANT` and various document-related descriptors suggests a structured approach to handling document content, emphasizing the importance of precise and context-aware processing. The `from_context` class method in `AbbreviatePageContentUserMessage` constructs a message by wrapping the user prompt and relevant document content, demonstrating a methodical approach to generating user-specific messages. Overall, this code provides a focused functionality within a broader system, aimed at enhancing the interaction between users and language models by ensuring that document content is preprocessed in a way that maximizes the LLM's efficiency and accuracy.
# Imports and Dependencies

---
- `shared.v3.globals.constants`
- `shared.v3.globals.glossary`
- `shared.v3.interfaces.llm_message`


# Global Variables

---
### content 
- **Type**: `str`
- **Description**: The `content` variable is a string that serves as a template for system messages in the `AbbreviatePageContentSystemMessage` class. It combines descriptions from various document components and instructions for processing document sections into a concise, information-dense format. This string is designed to guide the LLM in converting document sections into relevant context for agentic systems.
- **Use**: This variable is used to define the content of system messages that instruct the LLM on how to preprocess and structure document parts for effective downstream use.


---
### message_kind 
- **Type**: `MessageKind`
- **Description**: The `message_kind` variable is a global variable of type `MessageKind`, which is an enumeration imported from the `shared.v3.interfaces.llm_message` module. It is used to specify the kind of message being handled by the `AbbreviatePageContentSystemMessage` and `AbbreviatePageContentUserMessage` classes, indicating whether the message is a system or user message.
- **Use**: This variable is used to categorize messages as either system or user messages within the `AbbreviatePageContentSystemMessage` and `AbbreviatePageContentUserMessage` classes.


# Classes

---
### AbbreviatePageContentSystemMessage 
- **Type**: `class`
- **Members**:
    - `content`: A string that contains detailed instructions and context for processing document sections.
    - `message_kind`: Specifies the kind of message, set to MessageKind.SYSTEM.
- **Description**: The `AbbreviatePageContentSystemMessage` class is a specialized message class that inherits from `LlmMessage` and is designed to provide a structured and detailed context for processing document sections. It contains a `content` attribute that includes instructions for converting document sections into concise, information-dense summaries suitable for use by downstream language models. The class ensures that only relevant information is extracted and structured, helping to avoid unnecessary external searches and ensuring clarity and non-redundancy in technical documentation or explanations. The `message_kind` attribute is set to `MessageKind.SYSTEM`, indicating its role in the system's message processing.
- **Inherits From**:
    - LlmMessage


---
### AbbreviatePageContentUserMessage 
- **Type**: `class`
- **Members**:
    - `message_kind`: Specifies the kind of message, set to MessageKind.USER.
- **Description**: The `AbbreviatePageContentUserMessage` class is a specialized message class that inherits from `LlmMessage` and is used to create user messages that request a concise summary of document content based on a user prompt and cursor position. It includes a class method `from_context` that constructs the message content by wrapping the user prompt and relevant document sections, depending on the cursor's position, to generate a summary that is information-dense and contextually relevant.
- **Inherits From**:
    - LlmMessage

**Methods**

---
#### AbbreviatePageContentUserMessage.from_context
The `from_context` function creates an `AbbreviatePageContentUserMessage` instance with a content string summarizing relevant document parts based on a user prompt and cursor position.
- **Inputs**:
    - `cls`: The class reference to `AbbreviatePageContentUserMessage`, used to create a new instance.
    - `prompt`: A string representing the user's prompt that guides the summarization process.
    - `page_content`: A string containing the content of the page to be summarized.
    - `before`: A boolean indicating whether the cursor is positioned before the selected text in the document.
    - `selected_text`: An optional string representing the text selected by the user, which may be `None` if no text is selected.
- **Control Flow**:
    - Constructs a content string that includes a prompt for summarization and wraps the user prompt using `USER_PROMPT.wrap(prompt)`.
    - If `before` is `True`, it wraps the `page_content` using `DOCUMENT_CONTENT_BEFORE_CURSOR.wrap(page_content)` and includes it in the content string.
    - Wraps the `selected_text` using `CURSOR_SELECTION.wrap(selected_text)` and includes it in the content string.
    - If `before` is `False`, it wraps the `page_content` using `DOCUMENT_CONTENT_AFTER_CURSOR.wrap(page_content)` and includes it in the content string.
    - Strips any leading or trailing whitespace from the constructed content string.
    - Returns a new instance of `AbbreviatePageContentUserMessage` with the constructed content string.
- **Output**:
    - An instance of `AbbreviatePageContentUserMessage` with a content string summarizing the relevant parts of the document based on the user prompt and cursor position.



