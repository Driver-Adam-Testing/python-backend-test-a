# Purpose
This Python code defines an abstract base class `PipelineRequest` that serves as a foundational component for handling pipeline requests in a system that likely involves large language models (LLMs). The class is designed to manage sessions and data sources related to LLM operations, as indicated by its integration with `RuntimeLlmSession` and `DataSource` objects. The class constructor initializes these components based on various identifiers such as `llm_session_id`, `page_node_id`, and `organization_id`, and it interacts with a database to retrieve or create session information. The class also provides methods for running and streaming pipeline processes, which are abstract and intended to be implemented by subclasses, suggesting that this file is part of a larger framework or library that supports extensibility.

The code is structured to be part of a library or framework rather than a standalone script, as it defines a class with abstract methods and relies on external modules and interfaces. It imports several components from other parts of the system, such as `LlmClient` and `LlmStreamResponse`, indicating that it is part of a modular architecture. The class provides a public API through its methods and properties, allowing other parts of the system to interact with LLM sessions and data sources. The use of Pydantic's `BaseModel` for data validation and the integration with SQLModel for database operations highlight the code's focus on robust data handling and persistence.
# Imports and Dependencies

---
- `json`
- `abc`
- `collections.abc`
- `typing`
- `uuid`
- `modal`
- `database.db`
- `database.models_v2`
- `pydantic`
- `shared.v3`
- `shared.v3.interfaces.llm_stream_response`
- `shared.v3.utils.datasource`
- `shared.v3.utils.encoder`
- `sqlmodel`


# Global Variables

---
### _llm_session 
- **Type**: `RuntimeLlmSession | None`
- **Description**: The `_llm_session` variable is an instance of `RuntimeLlmSession` or `None`, used to manage and store the state of a language model session within the `PipelineRequest` class. It is initialized based on the provided `llm_session_id` or created anew if no valid session ID is provided. This variable is crucial for maintaining session-specific data such as organization ID, user ID, and source node IDs.
- **Use**: The `_llm_session` variable is used to track and manage the state of a language model session, ensuring that session-specific data is correctly initialized and stored.


# Classes

---
### PipelineRequest 
- **Type**: `class`
- **Members**:
    - `_datasource`: Holds the DataSource object associated with the request.
    - `_llm_session`: Stores the RuntimeLlmSession object or None if not initialized.
- **Description**: The `PipelineRequest` class is an abstract base class that extends `BaseModel` and is designed to handle the initialization and management of data sources and LLM sessions for a pipeline. It provides mechanisms to create a `DataSource` from various identifiers such as node IDs, relative paths, or page node IDs, and manages a `RuntimeLlmSession` either by retrieving an existing session or creating a new one. The class includes methods for running and streaming pipeline responses, which must be implemented by subclasses, as indicated by the abstract methods `_run` and `_stream`. It also provides properties to access the `datasource` and `llm_session` attributes.
- **Inherits From**:
    - BaseModel
    - ABC

**Methods**

---
#### PipelineRequest.__init__
The `__init__` function initializes a `PipelineRequest` object, setting up its data source and LLM session based on provided identifiers and paths.
- **Inputs**:
    - `llm_session_id`: An optional UUID representing the LLM session ID to retrieve an existing session.
    - `page_node_id`: An optional UUID representing the page node ID to create a data source from.
    - `organization_id`: An optional string representing the organization ID associated with the data source and session.
    - `user_id`: An optional string representing the user ID associated with the session.
    - `node_ids`: An optional list of UUIDs representing node IDs to create a data source from.
    - `relative_paths`: An optional list of strings representing relative paths to create a data source from.
    - `**data`: Additional keyword arguments passed to the superclass initializer.
- **Control Flow**:
    - The function calls the superclass initializer with any additional data provided.
    - It checks if `node_ids` is provided and initializes the data source using `DataSource.from_node_ids`.
    - If `node_ids` is not provided, it checks for `relative_paths` and initializes the data source using `DataSource.from_relative_paths`.
    - If neither `node_ids` nor `relative_paths` are provided, it checks for `page_node_id` and initializes the data source using `DataSource.from_page_id`.
    - If none of the above are provided, the data source is set to `None`.
    - A database session is opened using `get_session()`.
    - If `llm_session_id` is provided, it attempts to retrieve an existing LLM session from the database.
    - If a session is found and the data source is `None`, it initializes the data source using the session's source node IDs.
    - If no session is found or `llm_session_id` is not provided, a new `RuntimeLlmSession` is created and added to the database.
    - The session is committed and refreshed to ensure the latest data is available.
- **Output**:
    - The function does not return any value; it initializes the object's state.


---
#### PipelineRequest._run
The `_run` function is an abstract method intended to be overridden in subclasses, raising a `NotImplementedError` if not implemented.
- **Inputs**:
    - `client`: An optional `LlmClient` instance, defaulting to `None`, which may be used for executing the pipeline.
- **Control Flow**:
    - The function immediately raises a `NotImplementedError` with a message indicating that the method is not supported by the current pipeline.
- **Output**:
    - The function does not return any output as it raises an exception.


---
#### PipelineRequest._stream
The `_stream` function is an abstract asynchronous generator method intended to yield `LlmStreamResponse` objects, but it is not implemented in this pipeline.
- **Inputs**:
    - `client`: An optional `LlmClient` instance, defaulting to `None`, which may be used to interact with the LLM service.
- **Control Flow**:
    - The function is defined as an asynchronous generator, indicated by the `async def` and `AsyncGenerator` return type.
    - The function immediately raises a `NotImplementedError`, indicating that it is intended to be overridden in a subclass and is not implemented in this base class.
- **Output**:
    - The function is expected to yield `LlmStreamResponse` objects, but currently, it raises a `NotImplementedError` and does not produce any output.


---
#### PipelineRequest.datasource
The `datasource` function returns a `DataSource` object, initializing it if it hasn't been set yet.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if the `_datasource` attribute exists on the instance using `hasattr`.
    - If `_datasource` does not exist, initialize it using `DataSource.from_node_ids` with `self.node_ids` and `self.organization_id`.
    - Return the `_datasource` attribute.
- **Output**:
    - The function returns a `DataSource` object associated with the instance.


---
#### PipelineRequest.from_dict
The `from_dict` function creates an instance of the `PipelineRequest` class using a dictionary of data as keyword arguments.
- **Inputs**:
    - `data`: A dictionary containing the data to be used as keyword arguments for initializing a `PipelineRequest` object.
- **Control Flow**:
    - The function takes a dictionary `data` as input.
    - It unpacks the dictionary into keyword arguments using `**data`.
    - It calls the class constructor `cls` with these keyword arguments to create a new instance of `PipelineRequest`.
- **Output**:
    - An instance of the `PipelineRequest` class initialized with the provided dictionary data.


---
#### PipelineRequest.llm_session
The `llm_session` function returns the current `RuntimeLlmSession` instance associated with the `PipelineRequest` object.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a property method of the `PipelineRequest` class.
    - It directly returns the `_llm_session` attribute of the class instance.
- **Output**:
    - The function returns an instance of `RuntimeLlmSession`, which may be `None` if not set.


---
#### PipelineRequest.run
The `run` function executes the `_run` method of the `PipelineRequest` class, which is intended to be implemented by subclasses.
- **Inputs**:
    - `client`: An optional `LlmClient` instance that can be passed to the `_run` method, defaulting to `None`.
- **Control Flow**:
    - The function calls the `_run` method, passing the `client` argument if provided.
    - The `_run` method is abstract and must be implemented by subclasses of `PipelineRequest`.
- **Output**:
    - The function returns the result of the `_run` method, which is expected to be a `PipelineResponse` object.


---
#### PipelineRequest.stream
The `stream` function asynchronously generates a sequence of LlmStreamResponse objects, starting and ending with session-specific responses.
- **Inputs**:
    - `client`: An optional LlmClient instance used for the streaming process.
- **Control Flow**:
    - The function begins by yielding a StartSessionStreamResponse object, indicating the start of a session with the session ID and execution call ID.
    - It then enters an asynchronous loop, yielding each response from the `_stream` method, which is expected to be implemented in a subclass.
    - Finally, it yields an EndSessionStreamResponse object, indicating the end of the session with the session ID.
- **Output**:
    - An asynchronous generator yielding LlmStreamResponse objects, including start and end session responses.



