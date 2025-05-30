# Purpose
This Python code defines a module that provides functionality for handling chat interactions within a pipeline framework. It is designed to be part of a larger system, likely a conversational AI or chatbot application, where it manages the request and response flow for chat sessions. The module includes two primary classes: `ChatPipelineRequest` and `ChatPipelineResponse`. The `ChatPipelineRequest` class is responsible for managing the chat history, either by retrieving existing history from a database or initializing a new one with standard system messages. It also appends new user prompts to the history and interacts with an LLM (Large Language Model) client to generate responses. The `ChatPipelineResponse` class is a typed response object that encapsulates the final response and any references generated during the chat session.

The code is structured to support both synchronous and asynchronous operations, with methods for running the chat pipeline and streaming responses. It leverages various components from imported modules, such as database models, message types, and utility functions, to facilitate its operations. The module is intended to be part of a broader application, as indicated by its reliance on external interfaces and data models. It defines a public API through the `__all__` variable, which specifies the components available for import by other modules. Overall, this code provides a focused functionality for managing chat interactions within a pipeline, integrating with a database for history persistence, and utilizing an LLM client for generating conversational responses.
# Imports and Dependencies

---
- `__future__.annotations`
- `json`
- `typing.TYPE_CHECKING`
- `database.db.get_session`
- `database.models_v2.RuntimeLlmMessageHistory`
- `database.models_v2.RuntimeLlmSession`
- `database.models_v2_enums.LlmPipelineKind`
- `shared.v3.LlmClient`
- `shared.v3.LlmMessage`
- `shared.v3.LlmMessageHistory`
- `shared.v3.MessageKind`
- `shared.v3.app.pipelines.pipeline_request.PipelineRequest`
- `shared.v3.app.pipelines.pipeline_response.PipelineResponse`
- `shared.v3.app.static.messages.driver_app_messages.ChatContextMessage`
- `shared.v3.app.static.messages.driver_app_messages.ContentStructureMessage`
- `shared.v3.app.static.messages.driver_app_messages.DriverApplicationMessage`
- `shared.v3.app.static.messages.driver_app_messages.HowDriverWorksMessage`
- `shared.v3.app.static.messages.driver_app_messages.PromptGuidelinesMessage`
- `shared.v3.app.static.tools.hybrid_search.HybridSearchTool`
- `shared.v3.globals.datasource_messages.DataSourceMessage`
- `shared.v3.globals.datasource_messages.DataSourceSystemMessage`
- `shared.v3.globals.datasource_messages.DataSourceTuningSystemMessage`
- `shared.v3.interfaces.llm_stream_response.EndSessionStreamResponse`
- `shared.v3.interfaces.llm_stream_response.LlmStreamResponse`
- `shared.v3.interfaces.llm_stream_response.LlmStreamResponseKind`
- `shared.v3.interfaces.llm_stream_response.StartSessionStreamResponse`
- `shared.v3.utils.datasource.DataSource`
- `sqlmodel.select`
- `collections.abc.AsyncGenerator`
- `collections.abc.Sequence`


# Global Variables

---
### __all__ 
- **Type**: `Sequence[str]`
- **Description**: The `__all__` variable is a list of strings that defines the public interface of the module. It specifies which classes, functions, or variables should be accessible when the module is imported using a wildcard import (e.g., `from module import *`).
- **Use**: This variable is used to control the export of the `ChatPipelineRequest` and `ChatPipelineResponse` classes when the module is imported.


# Classes

---
### ChatPipelineRequest 
- **Type**: `class`
- **Members**:
    - `user_prompt`: A string representing the user's input prompt for the chat.
- **Description**: The `ChatPipelineRequest` class is designed to handle requests for the `/chat` endpoint, focusing on maintaining and utilizing chat history. It inherits from `PipelineRequest` and includes methods to retrieve or create a message history, run a chat session, and stream chat responses. The class ensures that user prompts are appended to the chat history, which is either retrieved from a database or initialized with standard system messages if no history exists. It interacts with an LLM client to process the chat and return responses, supporting both synchronous and asynchronous operations.
- **Inherits From**:
    - PipelineRequest

**Methods**

---
#### ChatPipelineRequest._get_or_create_message_history
The function `_get_or_create_message_history` retrieves or initializes a message history for a chat session and appends a new user message to it.
- **Inputs**:
    - None
- **Control Flow**:
    - Establish a database session using `get_session()`.
    - Attempt to retrieve an existing chat history ID from the database for the current session and pipeline kind.
    - If a chat history ID is found, load the message history from the database and initialize the data source if it is not already set.
    - If no chat history exists, create a new `LlmMessageHistory` with a set of standard system messages and associate it with the current session.
    - Append the current user prompt as a new message to the message history.
- **Output**:
    - The function returns an `LlmMessageHistory` object that includes the complete message history with the newly added user message.


---
#### ChatPipelineRequest._run
The `_run` function executes a chat pipeline by retrieving or creating a message history, performing multiple iterations of a client operation with a hybrid search tool, and returning a structured response with the final content and references.
- **Inputs**:
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.gpt_4o_chat()`, used to perform operations on the message history.
- **Control Flow**:
    - Call `_get_or_create_message_history` to retrieve or initialize the message history for the chat session.
    - Invoke `client.multi_shot` with the message history, specifying `HybridSearchTool` as the tool type, and perform 3 iterations using the provided datasource.
    - Extract the `information_response` and `called_tools` from the result of `client.multi_shot`.
    - Create a `ChatPipelineResponse` object with the content of `information_response` and a list of unique references extracted from `called_tools`.
    - Return the `ChatPipelineResponse` object.
- **Output**:
    - Returns a `ChatPipelineResponse` object containing the final response content and a list of unique references from the tools used.


---
#### ChatPipelineRequest._stream
The `_stream` function asynchronously streams responses from a language model client using a message history and specified tools.
- **Inputs**:
    - `self`: An instance of the `ChatPipelineRequest` class, which contains methods and attributes for managing chat sessions and message history.
    - `client`: An instance of `LlmClient`, defaulting to `LlmClient.gpt_4o_chat()`, which is used to interact with the language model for streaming responses.
- **Control Flow**:
    - Retrieve or create a message history using the `_get_or_create_message_history` method.
    - Yield a `StartSessionStreamResponse` to indicate the beginning of a session with the session ID.
    - Use an asynchronous for loop to iterate over chunks of responses from the `client.multi_shot_stream` method, which streams responses based on the message history, tool types, and datasource.
    - Yield each chunk received from the `multi_shot_stream` method.
    - Yield an `EndSessionStreamResponse` to indicate the end of the session with the session ID.
- **Output**:
    - An asynchronous generator that yields `LlmStreamResponse` objects, starting with a `StartSessionStreamResponse`, followed by streamed response chunks, and ending with an `EndSessionStreamResponse`.



---
### ChatPipelineResponse 
- **Type**: `class`
- **Description**: The `ChatPipelineResponse` class is a specialized response type for the chat pipeline, inheriting from `PipelineResponse`. It is designed to handle the final response and references generated by the chat pipeline, providing a structured way to manage these outputs.
- **Inherits From**:
    - PipelineResponse


