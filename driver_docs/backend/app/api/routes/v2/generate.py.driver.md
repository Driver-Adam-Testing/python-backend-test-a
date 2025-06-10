# Purpose
This Python file is a FastAPI application module that defines several API endpoints for content generation and editing. It primarily focuses on handling requests related to inline editing and content generation using different pipeline kinds, such as INLINE_EDIT, SMART_INSTRUCTION, REFORMAT, and CHAT. The module imports various components from external libraries and shared modules, including FastAPI for routing, Pydantic for request validation, and a custom modal library for remote function execution. The code defines several Pydantic models to structure incoming HTTP requests and responses, ensuring that the data is validated and processed correctly.

The file includes three main API endpoints: `/inline_edit`, `/attach/{call_id}`, and `/`. The `/inline_edit` endpoint performs inline editing on selected text, supporting both streaming and non-streaming responses, and can execute tasks remotely or locally. The `/attach/{call_id}` endpoint allows users to attach to a modal function call, providing streaming or non-streaming responses based on the request parameters. The root endpoint `/` is used for generating content based on a given prompt and context, utilizing different pipeline kinds and execution types. The code also defines several enumerations to manage pipeline kinds, execution types, and remote function names, facilitating the dynamic selection of processing logic based on the request parameters. Overall, this module serves as a backend service for content editing and generation, leveraging remote execution capabilities for scalability and flexibility.
# Imports and Dependencies

---
- `collections.abc`
- `enum`
- `uuid`
- `modal`
- `fastapi`
- `fastapi.responses`
- `pydantic`
- `shared.v3.app.pipelines`
- `shared.v3.app.static.enums.format_kinds`
- `app.api.auth`


# Global Variables

---
### CHAT 
- **Type**: `Enum`
- **Description**: `CHAT` is a member of the `PipelineKind` enumeration, representing a specific type of pipeline operation related to chat functionalities. It is used to categorize and handle requests that involve chat-based processing within the application.
- **Use**: `CHAT` is used to identify and execute chat-related pipeline operations, determining the appropriate request model and remote function to invoke.


---
### CHAT_RUN 
- **Type**: `str`
- **Description**: `CHAT_RUN` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function used for executing chat-related operations in a synchronous manner.
- **Use**: This variable is used to identify and call the specific remote function for synchronous chat execution within the application.


---
### CHAT_STREAM 
- **Type**: `str`
- **Description**: `CHAT_STREAM` is a member of the `RemoteFunctions` enumeration, which defines various remote function names used in the application. It represents the function name for streaming chat operations.
- **Use**: This variable is used to identify and call the specific remote function for streaming chat operations within the application.


---
### INLINE_EDIT 
- **Type**: `str`
- **Description**: `INLINE_EDIT` is a member of the `PipelineKind` enumeration, which is a subclass of `str` and `Enum`. It represents a specific type of pipeline operation that can be performed, specifically for inline editing tasks.
- **Use**: This variable is used to identify and differentiate the inline editing pipeline operation within the system.


---
### INLINE_EDIT_RUN 
- **Type**: `str`
- **Description**: `INLINE_EDIT_RUN` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function used for executing inline edit operations synchronously.
- **Use**: This variable is used to identify and call the specific remote function for inline editing when synchronous execution is required.


---
### INLINE_EDIT_STREAM 
- **Type**: `str`
- **Description**: `INLINE_EDIT_STREAM` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function used for streaming inline edit operations.
- **Use**: This variable is used to identify and call the specific remote function for streaming inline edit operations in the application.


---
### LOCAL 
- **Type**: `Enum`
- **Description**: `LOCAL` is a member of the `ExecutionType` enumeration, which defines different types of execution modes for processing requests. The `ExecutionType` enum includes options for remote asynchronous, remote synchronous, and local execution.
- **Use**: This variable is used to determine if a request should be executed locally, as opposed to being processed remotely.


---
### REFORMAT 
- **Type**: `Enum`
- **Description**: The `REFORMAT` variable is a member of the `PipelineKind` enumeration, which defines different types of pipeline operations that can be performed. It represents a specific kind of pipeline operation related to reformatting content.
- **Use**: This variable is used to identify and handle reformatting operations within the pipeline processing logic.


---
### REFORMAT_RUN 
- **Type**: `str`
- **Description**: `REFORMAT_RUN` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function used for executing a reformatting operation in a synchronous manner.
- **Use**: This variable is used to identify and call the specific remote function for reformatting operations when the execution type is synchronous.


---
### REFORMAT_STREAM 
- **Type**: `str`
- **Description**: `REFORMAT_STREAM` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function that handles streaming operations for reformatting tasks.
- **Use**: This variable is used to identify and call the specific remote function for streaming reformat operations in the application.


---
### REMOTE_ASYNC 
- **Type**: `Enum`
- **Description**: `REMOTE_ASYNC` is a member of the `ExecutionType` enumeration, which defines different modes of execution for processing requests. This enumeration is used to specify whether a request should be executed asynchronously on a remote server.
- **Use**: `REMOTE_ASYNC` is used to indicate that a request should be executed asynchronously on a remote server, allowing for non-blocking operations.


---
### REMOTE_SYNC 
- **Type**: `Enum`
- **Description**: `REMOTE_SYNC` is a member of the `ExecutionType` enumeration, which defines different modes of execution for processing requests. This enumeration is used to specify whether a request should be executed remotely in a synchronous manner, as opposed to asynchronously or locally.
- **Use**: `REMOTE_SYNC` is used to determine the execution mode for processing requests, specifically indicating that the request should be executed remotely and synchronously.


---
### SMART_INSTRUCTION 
- **Type**: `str`
- **Description**: `SMART_INSTRUCTION` is a member of the `PipelineKind` enumeration, which represents different types of pipeline operations that can be performed in the application. It is used to identify and handle operations related to smart instructions within the pipeline processing logic.
- **Use**: This variable is used to select the appropriate pipeline request model and remote function for smart instruction operations.


---
### SMART_INSTRUCTION_RUN 
- **Type**: `str`
- **Description**: `SMART_INSTRUCTION_RUN` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function used for executing smart instruction tasks synchronously.
- **Use**: This variable is used to identify and call the specific remote function for running smart instruction tasks without streaming.


---
### SMART_INSTRUCTION_STREAM 
- **Type**: `str`
- **Description**: `SMART_INSTRUCTION_STREAM` is a string constant defined in the `RemoteFunctions` enumeration. It represents the name of a remote function that handles streaming operations for smart instructions.
- **Use**: This variable is used to identify and call the appropriate remote function for streaming smart instruction operations.


---
### _PIPELINE_BUILDERS 
- **Type**: `dict[PipelineKind, Callable[[GenerateHttpRequest, UserToken], BaseModel]]`
- **Description**: _PIPELINE_BUILDERS is a dictionary that maps each PipelineKind to a corresponding function that constructs a specific request model. Each function takes a GenerateHttpRequest and a UserToken as input and returns a BaseModel instance. This setup allows for dynamic creation of request models based on the pipeline kind specified in the input.
- **Use**: This variable is used to determine which request model to build for a given PipelineKind when processing a GenerateHttpRequest.


---
### _REMOTE_FUNCTION_NAMES 
- **Type**: `dict[tuple[PipelineKind, bool], str]`
- **Description**: The `_REMOTE_FUNCTION_NAMES` variable is a dictionary that maps a tuple consisting of a `PipelineKind` and a boolean indicating streaming to a string representing the name of a remote function. This mapping is used to determine which remote function to call based on the type of pipeline and whether streaming is enabled.
- **Use**: This variable is used to look up the appropriate remote function name for execution based on the pipeline kind and streaming option.


---
### execution_type 
- **Type**: `Enum`
- **Description**: The `execution_type` variable is an instance of the `ExecutionType` enumeration, which defines the mode of execution for a given task. It can take one of three values: `REMOTE_ASYNC`, `REMOTE_SYNC`, or `LOCAL`, indicating whether the task should be executed asynchronously or synchronously on a remote server, or locally.
- **Use**: This variable is used to determine the execution strategy for processing requests in the `generate` function.


---
### format_kind 
- **Type**: `FormatKind`
- **Description**: The `format_kind` variable is an instance of the `FormatKind` enumeration, which is imported from the `shared.v3.app.static.enums.format_kinds` module. It is used to specify the format type for a given request, with a default value of `FormatKind.ANY`. This allows the system to handle different formatting requirements based on the context of the request.
- **Use**: This variable is used to determine the format type for processing requests in the `GenerateHttpRequest` model.


---
### pipeline_kind 
- **Type**: `PipelineKind`
- **Description**: The `pipeline_kind` variable is an instance of the `PipelineKind` enumeration, which defines different types of processing pipelines that can be used in the application. These types include INLINE_EDIT, SMART_INSTRUCTION, REFORMAT, and CHAT, each representing a specific kind of operation or transformation that can be performed on the input data.
- **Use**: This variable is used to determine which specific pipeline processing logic to apply when handling a request.


---
### remote_execution 
- **Type**: `bool`
- **Description**: The `remote_execution` variable is a boolean field within the `InlineEditHttpRequest` class, which is a Pydantic model. It indicates whether the inline editing operation should be executed remotely or not.
- **Use**: This variable is used to determine if the inline editing process should be handled by a remote function or executed locally within the `inline_edit` function.


---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints, allowing for modular and organized routing in a FastAPI application.
- **Use**: This variable is used to register and manage API routes for handling HTTP requests related to inline editing and content generation.


---
### stream 
- **Type**: `bool`
- **Description**: The `stream` variable is a boolean flag used to determine whether the response should be streamed or not. It is defined as a default parameter in the `attach_to_modal` function and as a field in the `InlineEditHttpRequest` and `GenerateHttpRequest` models.
- **Use**: This variable is used to control the flow of data, deciding between streaming responses or executing them in a non-streaming manner.


# Classes

---
### AsyncCallResponse 
- **Type**: `class`
- **Members**:
    - `llm_session_id`: A UUID representing the session ID for the language model.
    - `remote_execution_id`: A string representing the ID for the remote execution.
- **Description**: The `AsyncCallResponse` class is a simple data model that inherits from `BaseModel` and is used to encapsulate the response details of an asynchronous call, specifically holding a session ID and a remote execution ID.
- **Inherits From**:
    - BaseModel


---
### ExecutionType 
- **Type**: `class`
- **Members**:
    - `REMOTE_ASYNC`: Represents an asynchronous remote execution type.
    - `REMOTE_SYNC`: Represents a synchronous remote execution type.
    - `LOCAL`: Represents a local execution type.
- **Description**: The `ExecutionType` class is an enumeration that defines different modes of executing tasks, specifically distinguishing between remote asynchronous, remote synchronous, and local execution types. It inherits from both `str` and `Enum`, allowing it to be used as a string while also providing enumeration capabilities for better code readability and control flow.
- **Inherits From**:
    - str
    - Enum


---
### GenerateHttpRequest 
- **Type**: `class`
- **Members**:
    - `prompt`: A string representing the user's input or query.
    - `page_content_before_cursor`: A string representing the content before the cursor position.
    - `page_content_after_cursor`: A string representing the content after the cursor position.
    - `cursor_selection`: A string representing the selected text at the cursor.
    - `node_ids`: A list of UUIDs representing node identifiers.
    - `format_kind`: An instance of FormatKind enum specifying the format type, defaulting to FormatKind.ANY.
    - `stream`: A boolean indicating whether the response should be streamed, defaulting to True.
    - `pipeline_kind`: An instance of PipelineKind enum specifying the pipeline type, defaulting to PipelineKind.CHAT.
    - `execution_type`: An instance of ExecutionType enum specifying the execution type, defaulting to ExecutionType.REMOTE_ASYNC.
- **Description**: The GenerateHttpRequest class is a Pydantic model used to define the structure of HTTP requests for generating content. It includes fields for user input, context around a cursor, node identifiers, and various configuration options such as format kind, streaming preference, pipeline kind, and execution type. This class is designed to facilitate the generation of content by providing a structured way to pass necessary parameters to the backend processing functions.
- **Inherits From**:
    - BaseModel


---
### InlineEditHttpRequest 
- **Type**: `dataclass`
- **Members**:
    - `prompt`: A string representing the user's input or query.
    - `page_content_before_cursor`: A string representing the content of the page before the cursor position.
    - `page_content_after_cursor`: A string representing the content of the page after the cursor position.
    - `cursor_selection`: A string representing the text selected by the cursor.
    - `node_ids`: A list of UUIDs representing the nodes involved in the request.
    - `remote_execution`: A boolean indicating if the execution should be performed remotely, defaulting to True.
    - `stream`: A boolean indicating if the response should be streamed, defaulting to True.
- **Description**: The `InlineEditHttpRequest` class is a data model used to encapsulate the details of an inline edit request, including the user's prompt, the content surrounding the cursor, selected text, and node identifiers. It also specifies whether the request should be executed remotely and if the response should be streamed.
- **Inherits From**:
    - BaseModel


---
### PipelineKind 
- **Type**: `class`
- **Members**:
    - `INLINE_EDIT`: Represents the 'INLINE_EDIT' pipeline kind.
    - `SMART_INSTRUCTION`: Represents the 'SMART_INSTRUCTION' pipeline kind.
    - `REFORMAT`: Represents the 'REFORMAT' pipeline kind.
    - `CHAT`: Represents the 'CHAT' pipeline kind.
- **Description**: The `PipelineKind` class is an enumeration that defines different types of pipeline operations that can be performed, such as inline editing, smart instructions, reformatting, and chat. Each member of the enumeration corresponds to a specific kind of pipeline operation, represented as a string.
- **Inherits From**:
    - Enum


---
### RemoteFunctions 
- **Type**: `class`
- **Members**:
    - `INLINE_EDIT_RUN`: Represents the remote function for inline edit run.
    - `INLINE_EDIT_STREAM`: Represents the remote function for inline edit stream.
    - `SMART_INSTRUCTION_RUN`: Represents the remote function for smart instruction run.
    - `SMART_INSTRUCTION_STREAM`: Represents the remote function for smart instruction stream.
    - `REFORMAT_RUN`: Represents the remote function for reformat run.
    - `REFORMAT_STREAM`: Represents the remote function for reformat stream.
    - `CHAT_RUN`: Represents the remote function for chat run.
    - `CHAT_STREAM`: Represents the remote function for chat stream.
- **Description**: The `RemoteFunctions` class is an enumeration that defines a set of string constants representing different remote function names used in the application. These constants are used to identify specific remote operations such as inline editing, smart instruction processing, reformatting, and chat functionalities, each with options for running or streaming the operations.
- **Inherits From**:
    - str
    - Enum


# Functions

---
### attach_to_modal 
The `attach_to_modal` function attaches to a modal function call using a given call ID and optionally streams the response.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `call_id`: A string representing the unique identifier of the modal function call to attach to.
    - `stream`: A boolean indicating whether the response should be streamed (default is `True`).
- **Control Flow**:
    - The function retrieves a `FunctionCall` object from the `modal` library using the provided `call_id` and the `stream` flag to determine if it is a generator.
    - If `stream` is `True`, the function returns a `StreamingResponse` with the generator obtained from `function_call.get_gen()`, setting the media type to `text/event-stream`.
    - If `stream` is `False`, the function returns the result of `function_call.get()`.
- **Output**:
    - The function returns either a `StreamingResponse` object if streaming is enabled, or the result of the function call if streaming is disabled.


---
### generate 
The `generate` function asynchronously generates content based on a given prompt and context, using either local or remote execution pipelines.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `input`: A `GenerateHttpRequest` object containing the prompt, context, and execution details for content generation.
- **Control Flow**:
    - The function begins by parsing the input using a pipeline builder specific to the `pipeline_kind` specified in the `input` parameter.
    - If the `execution_type` is `LOCAL`, it either streams or runs the parsed input locally, returning a `StreamingResponse` if streaming is enabled.
    - If the `execution_type` is not `LOCAL`, it determines the appropriate remote function name based on the `pipeline_kind` and `stream` attributes.
    - It retrieves a remote function using `modal.Function.from_name` with the determined function name.
    - If streaming is enabled, it returns a `StreamingResponse` from the remote function's `remote_gen` method.
    - If streaming is not enabled, it checks if the execution type is `REMOTE_ASYNC` and either spawns or directly calls the remote function with the parsed input.
- **Output**:
    - The function returns either an `AsyncCallResponse`, a `PipelineResponse`, or `None`, depending on the execution type and streaming options.


---
### inline_edit 
The `inline_edit` function performs inline editing on selected text, potentially using remote execution and streaming responses.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, containing user-specific information such as organization ID and user ID.
    - `input`: An `InlineEditHttpRequest` object containing details about the editing request, including the prompt, page content before and after the cursor, cursor selection, node IDs, and flags for remote execution and streaming.
- **Control Flow**:
    - Create an `InlineEditPipelineRequest` object `parsed_input` using data from `input` and `user`.
    - Check if `input.stream` is `True`.
    - If `input.stream` is `True`, print the stream status and check if `input.remote_execution` is `True`.
    - If both `input.stream` and `input.remote_execution` are `True`, return a `StreamingResponse` using a remote function call to `inline_edit_stream`.
    - If `input.stream` is `True` but `input.remote_execution` is `False`, return a `StreamingResponse` using the local `stream` method of `parsed_input`.
    - If `input.stream` is `False`, check if `input.remote_execution` is `True`.
    - If `input.stream` is `False` and `input.remote_execution` is `True`, return the result of a remote function call to `inline_edit_run`.
    - If both `input.stream` and `input.remote_execution` are `False`, return the result of the local `run` method of `parsed_input`.
- **Output**:
    - The function returns an `InlineEditPipelineResponse` object or `None`, depending on the execution path and whether the operation is performed locally or remotely.


