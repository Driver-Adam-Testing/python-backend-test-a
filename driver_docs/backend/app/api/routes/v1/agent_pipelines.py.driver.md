# Purpose
This Python file is a FastAPI-based module that defines a set of API endpoints for executing agent sequences in a modal environment. The primary functionality revolves around handling different types of block kinds, such as text, list, code, diagram, and table, and executing corresponding agent sequences. The file imports various components from shared interfaces and pipelines, indicating a modular design where specific tasks are delegated to specialized functions. The endpoints include synchronous and asynchronous execution of agent sequences, with the ability to handle batch requests and retrieve execution results. The use of Pydantic models, such as `AgentRunRequest`, ensures structured data handling and validation for incoming requests.

The file defines several API routes using FastAPI's `APIRouter`, each with specific permissions and functionalities. The `/dep` and `/async` endpoints initiate the execution of agent sequences, with the latter supporting asynchronous operations. The `/async/{call_id}` endpoint retrieves the results of an asynchronous execution, while the `/async/batch` endpoint handles batch processing of multiple asynchronous calls. The `/sync` endpoint provides a synchronous execution option. The code leverages the `modal` library for managing function calls and instances, indicating a distributed or cloud-based execution model. Overall, this file serves as a critical component in a larger system, facilitating the execution and management of complex agent sequences through a well-defined API.
# Imports and Dependencies

---
- `uuid`
- `fastapi`
- `modal`
- `pydantic`
- `shared.interfaces.agents.block_kind`
- `shared.interfaces.agents.pipeline_configuration`
- `shared.interfaces.request`
- `shared.interfaces.response`
- `shared.pipelines.agents.execute`
- `shared.pipelines.block_kind_pipelines.code`
- `shared.pipelines.block_kind_pipelines.diagram`
- `shared.pipelines.block_kind_pipelines.list`
- `shared.pipelines.block_kind_pipelines.table`
- `shared.prompts.block_kind.block_kind_any`
- `shared.prompts.block_kind.block_kind_code`
- `shared.prompts.block_kind.block_kind_diagram`
- `shared.prompts.block_kind.block_kind_list`
- `shared.prompts.block_kind.block_kind_table`
- `shared.prompts.block_kind.block_kind_text`
- `app.api.auth`
- `app.api.session`


# Global Variables

---
### block_kind 
- **Type**: `BlockKind | None`
- **Description**: The `block_kind` variable is an optional attribute of the `AgentRunRequest` class, which is a subclass of `PromptWithContext`. It is used to specify the type of block that the agent should process, such as text, list, code, diagram, or table. The `BlockKind` type is likely an enumeration that defines these possible block types.
- **Use**: This variable is used to determine the appropriate response format and execution path for processing different types of content blocks in the agent sequence.


---
### node_ids 
- **Type**: `list[UUID] | None`
- **Description**: The `node_ids` variable is a list of UUIDs that can be optionally included in the `AgentRunRequest` class. It represents a collection of unique identifiers for nodes that may be involved in the execution of an agent sequence.
- **Use**: This variable is used to specify which nodes are included in the data scope for executing agent sequences.


---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a set of routes for the application, allowing for modular and organized route management.
- **Use**: This variable is used to register and manage API endpoints for the application, facilitating the handling of HTTP requests.


---
### steps 
- **Type**: `list[PipelineStepConfiguration]`
- **Description**: The `steps` variable is a list of `PipelineStepConfiguration` objects, which define the configuration for each step in a pipeline. It is initialized with a default step configuration using the `PipelineStepType.DEFAULT` type.
- **Use**: This variable is used to store and manage the sequence of steps that will be executed in a pipeline process.


# Classes

---
### AgentRunRequest 
- **Type**: `class`
- **Members**:
    - `steps`: A list of pipeline step configurations with a default step type of DEFAULT.
    - `node_ids`: An optional list of UUIDs representing node identifiers.
    - `block_kind`: An optional BlockKind indicating the type of block to be processed.
- **Description**: The `AgentRunRequest` class is a data model that extends `PromptWithContext` and is used to encapsulate the configuration for running an agent sequence. It includes a list of pipeline step configurations, optional node identifiers, and an optional block kind to specify the type of block to be processed. This class is utilized in API endpoints to initiate and manage the execution of agent sequences, providing a structured way to pass necessary parameters and configurations.
- **Inherits From**:
    - PromptWithContext


---
### BatchInput 
- **Type**: `class`
- **Members**:
    - `call_ids`: A list of strings representing call IDs.
- **Description**: The `BatchInput` class is a simple data model that inherits from `BaseModel` and is used to encapsulate a list of call IDs. This class is likely used to handle batch processing of asynchronous function calls, where each call ID corresponds to a specific function execution instance.
- **Inherits From**:
    - BaseModel


# Functions

---
### execute_agent_sequence 
The `execute_agent_sequence` function executes a sequence of operations based on the specified block kind and user input, returning a pipeline response.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, containing user-specific information such as organization ID and user ID.
    - `session`: A `CurrentSession` object representing the current session context.
    - `input`: An `AgentRunRequest` object containing the input parameters for the agent run, including prompt, context, steps, node IDs, and block kind.
- **Control Flow**:
    - A dictionary `block_kind_to_response_format` maps each `BlockKind` to its corresponding response format class.
    - The `response_format` is determined by looking up the `input.block_kind` in the dictionary, defaulting to `BlockKindCopyEditorAny` if not specified.
    - A `PipelineInput` object is created using the input parameters and the determined `response_format`.
    - The function checks the `input.block_kind` and calls the corresponding block agent execution function (`execute_list_block_agent`, `execute_table_block_agent`, `execute_diagram_block_agent`, `execute_code_block_agent`) if it matches a specific block kind.
    - If the `input.block_kind` does not match any specific block kind, the `execute_sequence` function is called with the `pipeline_input`.
- **Output**:
    - The function returns a `PipelineResponse` object, which is the result of executing the specified agent sequence.


---
### execute_agent_sequence_modal_async 
The function `execute_agent_sequence_modal_async` initiates an asynchronous execution of an agent sequence using a modal function and returns a response with the call ID.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, containing user-specific information such as organization ID and user ID.
    - `input`: An `AgentRunRequest` object containing the details of the agent run, including the prompt, context, steps, node IDs, and block kind.
    - `session`: A `CurrentSession` object representing the current session context, though it is not used directly in the function.
- **Control Flow**:
    - A dictionary `block_kind_to_response_format` maps different block kinds to their corresponding response format classes.
    - The function retrieves the appropriate response format based on the `block_kind` from the `input`, defaulting to `BlockKindCopyEditorAny` if not specified.
    - A `PipelineInput` object is created using the input data, including prompt, context, steps, and a `DataScope` object with node IDs, organization ID, and user ID.
    - The function looks up a modal function named 'agent' with the action 'run'.
    - The modal function is spawned with the `PipelineInput`, creating an instance of the function call.
    - The function returns a `DriverModalResponse` object containing the call ID of the spawned instance.
- **Output**:
    - A `DriverModalResponse` object containing the call ID of the spawned modal function instance, which can be used to track the execution status.


---
### execute_agent_sequence_modal_sync 
The `execute_agent_sequence_modal_sync` function synchronously executes an agent sequence by transforming the input request into a pipeline input and invoking a remote modal function.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, containing information such as organization ID and user ID.
    - `input`: An `AgentRunRequest` object containing the steps to execute and optional node IDs for the data scope.
- **Control Flow**:
    - Transform the `AgentRunRequest` input into a `PipelineInput` object, setting the steps and data scope with node IDs, organization ID, and user ID.
    - Look up the modal function named 'run' in the 'agent' namespace using `Function.lookup`.
    - Invoke the remote modal function with the `pipeline_input` as an argument.
    - Return the result of the remote function call.
- **Output**:
    - A `PipelineResponse` object containing the result of the executed agent sequence.


---
### get_batch_execution_results 
The `get_batch_execution_results` function retrieves the execution results of multiple asynchronous function calls based on their call IDs.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `input`: A `DriverModalBatchRequest` object containing a list of call IDs for which execution results are to be retrieved.
- **Control Flow**:
    - Initialize an empty dictionary `results` to store the execution results for each call ID.
    - Iterate over each `call_id` in `input.call_ids`.
    - For each `call_id`, retrieve the corresponding `FunctionCall` object using `FunctionCall.from_id(call_id)`.
    - Attempt to get the result of the function call with a timeout of 0 seconds using `function_call.get(timeout=0)`.
    - If the result is successfully retrieved, store it in the `results` dictionary with the status 'completed'.
    - If a `TimeoutError` occurs, store a status of 'running' with no response in the `results` dictionary.
    - If any other exception occurs, store a status of 'expired' with the exception message as the error in the `results` dictionary.
    - Return the `results` dictionary containing the execution status and results for each call ID.
- **Output**:
    - A dictionary where each key is a call ID and each value is another dictionary containing the call ID, status ('completed', 'running', or 'expired'), the response (if available), and any error message.


---
### get_execution_results 
The `get_execution_results` function retrieves the execution results of a function call using a given call ID.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `call_id`: A string representing the unique identifier of the function call whose results are to be retrieved.
- **Control Flow**:
    - The function retrieves a `FunctionCall` object using the `from_id` method with the provided `call_id`.
    - It then calls the `get` method on the `FunctionCall` object with a timeout of 0 to immediately retrieve the result of the function call.
    - Finally, it returns the result obtained from the `FunctionCall` object.
- **Output**:
    - The function returns a `PipelineResponse` object containing the results of the function call.


