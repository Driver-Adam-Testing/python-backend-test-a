# Purpose
This Python code defines a specialized component within a larger application framework, specifically focusing on the functionality of reformatting text based on a specified format kind. The file introduces two primary classes, `ReformatPipelineRequest` and `ReformatPipelineResponse`, which extend from `PipelineRequest` and `PipelineResponse`, respectively. The `ReformatPipelineRequest` class is designed to handle requests for reformatting text, utilizing a language model client (`LlmClient`) to process the request. It includes methods for both synchronous (`_run`) and asynchronous (`_stream`) operations, allowing for flexibility in how the reformatting task is executed. The class leverages a message history composed of various system messages to guide the language model in performing the reformatting task, indicating a structured approach to interacting with the language model.

The code is part of a broader system, as evidenced by its reliance on shared components and interfaces, such as `LlmClient`, `LlmMessageHistory`, and various message classes. It is intended to be integrated into a larger application, likely as a module that provides reformatting capabilities. The use of specific format kinds, as indicated by the `FormatKind` enumeration, suggests that the reformatting process is customizable and can be tailored to different formatting requirements. This file does not define a public API or external interface directly but rather contributes to the internal workings of a pipeline system that processes and reformats text using advanced language model techniques.
# Imports and Dependencies

---
- `collections.abc.AsyncGenerator`
- `shared.v3.LlmClient`
- `shared.v3.LlmMessageHistory`
- `shared.v3.app.pipelines.pipeline_request.PipelineRequest`
- `shared.v3.app.pipelines.pipeline_response.PipelineResponse`
- `shared.v3.app.static.enums.format_kinds.FormatKind`
- `shared.v3.app.static.messages.copy_editor_messages.CopyEditorSystemMessage`
- `shared.v3.app.static.messages.format_kind_message.FormatKindMessage`
- `shared.v3.app.static.messages.software_expertise.SoftwareExpertiseMessage`
- `shared.v3.globals.global_messages.GlobalSystemMessage`
- `shared.v3.interfaces.llm_stream_response.LlmStreamResponse`


# Classes

---
### ReformatPipelineRequest 
- **Type**: `class`
- **Members**:
    - `cursor_selection`: A string representing the text selection to be reformatted.
    - `format_kind`: An instance of FormatKind indicating the desired format type.
- **Description**: The ReformatPipelineRequest class is a specialized type of PipelineRequest designed to handle text reformatting tasks. It utilizes a language model client to process a given text selection, specified by the 'cursor_selection' attribute, and reformats it according to the 'format_kind' attribute. The class provides both synchronous and asynchronous methods for executing the reformatting operation, leveraging a message history that includes system and expertise messages to guide the language model's response.
- **Inherits From**:
    - PipelineRequest

**Methods**

---
#### ReformatPipelineRequest._run
The `_run` function sends a reformatting request to an LLM client and returns the response as a `ReformatPipelineResponse`.
- **Inputs**:
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.gpt_4_1()`, used to send the reformatting request.
- **Control Flow**:
    - The function constructs a `LlmMessageHistory` object with a series of system messages, including global, copy editor, software expertise, and format kind messages.
    - It sends a single-shot request to the provided LLM client with a prompt to reformat the text specified in `self.cursor_selection`.
    - The response from the LLM client is captured and used to create a `ReformatPipelineResponse` object, which is then returned.
- **Output**:
    - A `ReformatPipelineResponse` object containing the reformatted content and an empty list of references.


---
#### ReformatPipelineRequest._stream
The `_stream` function asynchronously streams reformatted text chunks from a language model client based on a given cursor selection and format kind.
- **Inputs**:
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.o3_mini()`, which is used to interact with the language model.
- **Control Flow**:
    - The function is defined as an asynchronous generator, allowing it to yield results over time.
    - It calls the `single_shot_stream` method on the provided `client`, passing a `message_history` and a `prompt`.
    - The `message_history` is constructed with a series of system messages, including global, copy editor, software expertise, and a format kind message derived from the instance's `format_kind`.
    - The `prompt` is a formatted string instructing the reformatting of the text specified by `self.cursor_selection`.
    - The function asynchronously iterates over the chunks produced by `single_shot_stream`, yielding each chunk as it is received.
- **Output**:
    - The function yields chunks of `LlmStreamResponse` objects, which represent parts of the reformatted text.



---
### ReformatPipelineResponse 
- **Type**: `class`
- **Description**: The `ReformatPipelineResponse` class is a subclass of `PipelineResponse` and serves as a placeholder for responses specifically related to the reformatting pipeline, but it does not add any additional functionality or attributes beyond its parent class.
- **Inherits From**:
    - PipelineResponse


