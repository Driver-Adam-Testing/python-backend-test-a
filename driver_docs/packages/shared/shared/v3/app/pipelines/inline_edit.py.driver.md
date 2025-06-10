# Purpose
This Python code defines a specialized component of a larger system, specifically focusing on handling inline editing requests within a pipeline architecture. The file introduces two main classes: `InlineEditPipelineRequest` and `InlineEditPipelineResponse`, which extend from `PipelineRequest` and `PipelineResponse`, respectively. The `InlineEditPipelineRequest` class is designed to process user prompts and page content around a cursor position, utilizing a language model client (`LlmClient`) to generate responses. The class includes methods for both synchronous (`_run`) and asynchronous (`_stream`) processing, leveraging a multi-shot interaction with the language model to refine and generate content based on the user's input and context. The code integrates various message types and tools, such as `HybridSearchTool`, to facilitate the editing process, indicating a focus on enhancing user interaction with text content through AI-driven suggestions and edits.

The file is part of a broader application, as evidenced by its imports from shared modules and its reliance on a structured message history to interact with the language model. It is not a standalone script but rather a component intended to be integrated into a larger system, likely as part of a library or service that provides text editing capabilities. The code defines internal logic for processing requests and generating responses, but it does not expose a public API or external interface directly. Instead, it serves as a backend component that other parts of the application can utilize to perform inline text editing tasks, leveraging advanced language model capabilities.
# Imports and Dependencies

---
- `collections.abc.AsyncGenerator`
- `shared.v3.LlmClient`
- `shared.v3.LlmMessageHistory`
- `shared.v3.app.pipelines.abbreviate_page_content.abbreviate_page_content`
- `shared.v3.app.pipelines.pipeline_request.PipelineRequest`
- `shared.v3.app.pipelines.pipeline_response.PipelineResponse`
- `shared.v3.app.static.messages.copy_editor_messages.CopyEditorSystemMessage`
- `shared.v3.app.static.messages.inline_edit_messages.InlineEditSystemMessage`
- `shared.v3.app.static.messages.inline_edit_messages.InlineEditToolUseMessage`
- `shared.v3.app.static.messages.inline_edit_messages.InlineEditUserMessage`
- `shared.v3.app.static.messages.software_expertise.SoftwareExpertiseMessage`
- `shared.v3.app.static.tools.hybrid_search.HybridSearchTool`
- `shared.v3.globals.datasource_messages.DataSourceMessage`
- `shared.v3.globals.global_messages.GlobalSystemMessage`
- `shared.v3.interfaces.llm_stream_response.LlmStreamResponse`


# Classes

---
### InlineEditPipelineRequest 
- **Type**: `class`
- **Members**:
    - `user_prompt`: A string representing the user's input or query.
    - `page_content_before_cursor`: A string representing the content of the page before the cursor position.
    - `page_content_after_cursor`: A string representing the content of the page after the cursor position.
    - `cursor_selection`: A string representing the text selected by the cursor.
- **Description**: The `InlineEditPipelineRequest` class is a specialized request handler that extends `PipelineRequest` to facilitate inline editing operations using a language model client. It processes user prompts and page content around a cursor position to generate a response through the `_run` method, which performs a multi-shot interaction with the language model. The class also supports asynchronous streaming of responses via the `_stream` method, allowing for real-time interaction with the language model. The class leverages message history and tool types to manage the context and tools used during the language model interaction.
- **Inherits From**:
    - PipelineRequest

**Methods**

---
#### InlineEditPipelineRequest._run
The `_run` function processes a user prompt and page content to generate an inline edit response using a language model client.
- **Inputs**:
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.gpt_4_1()`, used to interact with the language model.
- **Control Flow**:
    - Abbreviate the page content before and after the cursor using the `abbreviate_page_content` function with the user prompt and page content.
    - Create a message history for the language model client using various system and user messages, including the abbreviated page content and user prompt.
    - Invoke the `multi_shot` method on the `client` with the constructed message history, specifying `HybridSearchTool` as the tool type, and iterate twice over the datasource.
    - Collect the response content and references from the tools used during the `multi_shot` execution.
    - Return an `InlineEditPipelineResponse` containing the final response content and a list of unique references.
- **Output**:
    - An `InlineEditPipelineResponse` object containing the final response content from the language model and a list of unique references from the tools used.


---
#### InlineEditPipelineRequest._stream
The `_stream` function asynchronously streams responses from a language model client using a multi-shot approach with a customized message history and tool types.
- **Inputs**:
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.o3_mini()`, which is used to interact with the language model.
- **Control Flow**:
    - The function begins by abbreviating the page content using the `abbreviate_page_content` function, which takes the user prompt and page content before and after the cursor as inputs.
    - It then constructs a `LlmMessageHistory` object with a series of predefined system and user messages, including the abbreviated page content and user prompt.
    - The function enters an asynchronous loop where it calls `client.multi_shot_stream` with the constructed message history, specified tool types, iterations, and datasource.
    - For each chunk of response received from the `multi_shot_stream`, the function yields the chunk, allowing the caller to process the streamed data incrementally.
- **Output**:
    - An asynchronous generator that yields `LlmStreamResponse` objects, representing chunks of the streamed response from the language model.



---
### InlineEditPipelineResponse 
- **Type**: `class`
- **Description**: The `InlineEditPipelineResponse` class is a subclass of `PipelineResponse` and currently does not add any additional functionality or attributes to its parent class. It serves as a specific type of response within the pipeline framework, likely intended for use in scenarios involving inline editing operations.
- **Inherits From**:
    - PipelineResponse


