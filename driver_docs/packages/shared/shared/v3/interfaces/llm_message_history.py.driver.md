# Purpose
The provided Python code defines a class `LlmMessageHistory`, which serves as a container for managing a sequence of `LlmMessage` objects. These objects represent a conversation or a sequence of instructions and responses, typically in the context of a language model interaction. The class provides methods to add, remove, and manipulate messages within this history, as well as to convert the message history into various formats compatible with different APIs, such as OpenAI's strict, O1, O3, and Anthropic APIs. This conversion is crucial for interfacing with these APIs, as each requires specific message formats and roles.

The class also includes functionality for persisting message histories to a database using SQLAlchemy and SQLModel, allowing for retrieval and storage of message sequences. It supports operations like loading message histories from the database, cleaning the history by removing specific types of messages, and creating deep copies of the message history. The class is designed to be used in environments where tracking and managing conversational history is essential, such as in chatbots or automated customer service systems, and it provides a structured way to handle and transform message data for various external interfaces.
# Imports and Dependencies

---
- `uuid`
- `database.db`
- `database.models_v2`
- `database.models_v2_enums`
- `openai.types.chat`
- `openai.types.chat.chat_completion_message_tool_call_param`
- `shared.v3.interfaces.llm_message`
- `shared.v3.interfaces.llm_message_kind`
- `sqlalchemy.orm`
- `sqlmodel`


# Classes

---
### LlmMessageHistory 
- **Type**: `class`
- **Members**:
    - `id`: Unique identifier for the message history.
    - `llm_session_id`: Identifier for the LLM session associated with the message history.
    - `pipeline_kind`: Specifies the kind of LLM pipeline used.
    - `debug`: Flag to enable or disable debug mode.
    - `messages`: List of LlmMessage objects representing the message history.
- **Description**: The `LlmMessageHistory` class serves as a container for managing a sequence of `LlmMessage` objects, which represent a conversation or a series of instructions and responses. It provides methods to add, remove, and manipulate messages, as well as convert them into formats suitable for various APIs like OpenAI and Anthropic. The class also supports loading message histories from a database and offers functionality to clean up specific types of messages, such as iteration or parsing description messages. Additionally, it can create a deep copy of itself and retrieve the last message in the history.

**Methods**

---
#### LlmMessageHistory.__init__
The `__init__` function initializes an instance of the `LlmMessageHistory` class, setting up its attributes and optionally populating it with messages.
- **Inputs**:
    - `messages`: A list of `LlmMessage` objects to initialize the message history with, or `None` if no initial messages are provided.
    - `id`: A `UUID` representing the unique identifier for the message history, or `None` if it should be generated.
    - `llm_session_id`: A `UUID` representing the session identifier for the LLM session, or `None` if not applicable.
    - `pipeline_kind`: An instance of `LlmPipelineKind` indicating the type of pipeline to use, defaulting to `LlmPipelineKind.DEFAULT`.
    - `debug`: A boolean flag indicating whether to enable debug mode, defaulting to `True`.
- **Control Flow**:
    - Assigns the provided `id`, `llm_session_id`, `pipeline_kind`, and `debug` to the instance attributes.
    - Checks if `id` is `None` and `llm_session_id` is not `None`; if so, it creates a new `RuntimeLlmMessageHistory` in the database and assigns its `id` to the instance.
    - Initializes `self.messages` as an empty list.
    - If `messages` is provided, iterates over each message and adds it to the message history using the `add_message` method.
- **Output**:
    - The function does not return any value; it initializes the instance attributes and potentially modifies the database.


---
#### LlmMessageHistory._remove_iteration_messages
The function `_remove_iteration_messages` removes all messages of kind `ITERATION` from the message history.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over each message in the `self.messages` list.
    - Checks if the `message_kind` of the current message is `MessageKind.ITERATION`.
    - If the condition is true, calls `self.remove_message(message)` to remove the message from the history.
- **Output**:
    - The function does not return any value; it modifies the `self.messages` list in place by removing messages of kind `ITERATION`.


---
#### LlmMessageHistory._remove_parsing_description_messages
The function `_remove_parsing_description_messages` removes all messages of kind `PARSING_DESCRIPTION` from the message history.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over each message in the `self.messages` list.
    - Checks if the `message_kind` of the current message is `MessageKind.PARSING_DESCRIPTION`.
    - If the condition is true, calls `self.remove_message(message)` to remove the message from the history.
- **Output**:
    - The function does not return any value; it modifies the `self.messages` list in place by removing certain messages.


---
#### LlmMessageHistory.add_message
The `add_message` function adds a new `LlmMessage` to the message history, optionally persists it to a database, and can print it to the console for debugging.
- **Inputs**:
    - `message`: An instance of `LlmMessage` to be added to the message history.
    - `debug`: A boolean flag indicating whether to print the message to the console for debugging purposes, defaulting to `True`.
- **Control Flow**:
    - Check if the message's hash is already in the message history; if so, return without adding it.
    - Append the message to the `messages` list if it is not already present.
    - If `llm_session_id`, `id`, and `message.persist` are all truthy, create a `RuntimeLlmMessage` object and persist it to the database using a session.
    - If `debug` is `True`, print the message to the console.
    - Return the `LlmMessageHistory` instance itself.
- **Output**:
    - Returns the `LlmMessageHistory` instance, allowing for method chaining.


---
#### LlmMessageHistory.clean
The `clean` function removes all iteration and parsing description messages from the message history.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `_remove_iteration_messages` to remove all messages of kind `ITERATION` from the message history.
    - The function calls `_remove_parsing_description_messages` to remove all messages of kind `PARSING_DESCRIPTION` from the message history.
- **Output**:
    - The function does not return any value; it modifies the message history in place.


---
#### LlmMessageHistory.copy
The `copy` function creates a deep copy of an `LlmMessageHistory` instance, including all its messages.
- **Inputs**:
    - None
- **Control Flow**:
    - Iterates over each message in the `self.messages` list.
    - Calls the `model_copy` method on each message to create a deep copy of it.
    - Creates a new `LlmMessageHistory` instance with the copied messages and `debug` set to `False`.
- **Output**:
    - A new `LlmMessageHistory` instance with a deep copy of the original messages.


---
#### LlmMessageHistory.from_db
The `from_db` function loads a message history from the database using a given UUID and returns it as an `LlmMessageHistory` object.
- **Inputs**:
    - `message_history_id`: A UUID representing the unique identifier of the message history to be loaded from the database.
- **Control Flow**:
    - The function begins by opening a database session using `get_session()`.
    - It executes a query to select a `RuntimeLlmMessageHistory` object from the database where the `id` matches the provided `message_history_id`, and preloads associated messages using `selectinload`.
    - If no matching `RuntimeLlmMessageHistory` is found, a `ValueError` is raised indicating the message history was not found.
    - If a matching record is found, an `LlmMessageHistory` object is instantiated with the retrieved `id`, `llm_session_id`, and `pipeline_kind`.
    - The messages from the `RuntimeLlmMessageHistory` are converted into `LlmMessage` objects and assigned to the `messages` attribute of the `LlmMessageHistory` instance.
    - The populated `LlmMessageHistory` object is returned.
- **Output**:
    - An `LlmMessageHistory` object populated with messages and metadata from the database.


---
#### LlmMessageHistory.last
The `last` function returns the last message in the message history.
- **Inputs**:
    - None
- **Control Flow**:
    - Accesses the `messages` list attribute of the `LlmMessageHistory` instance.
    - Returns the last element of the `messages` list using the index `-1`.
- **Output**:
    - The function returns an `LlmMessage` object, which is the last message in the `messages` list of the `LlmMessageHistory` instance.


---
#### LlmMessageHistory.remove_message
The `remove_message` function removes a specified `LlmMessage` from the message history and deletes its persisted record from the database if applicable.
- **Inputs**:
    - `message`: An instance of `LlmMessage` that is to be removed from the message history.
- **Control Flow**:
    - The function first removes the `message` from the `self.messages` list.
    - It checks if `llm_session_id`, `id`, and `message.persist` are truthy to determine if the message should also be removed from the database.
    - If the conditions are met, it opens a database session using `get_session()`.
    - Within the session, it executes a SQL delete command to remove the message from the `RuntimeLlmMessage` table where the `llm_message_json` matches the JSON representation of the message and the `message_history_id` matches `self.id`.
    - Finally, it commits the transaction to persist the changes in the database.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### LlmMessageHistory.to_anthropic
The `to_anthropic` function converts a message history into a format suitable for the Anthropic API by organizing messages into a list and combining system messages into a single string.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize empty lists for `messages` and `system_messages`.
    - Iterate over each message in `self.messages`.
    - Use a match statement to determine the `message_kind` of each message.
    - For `SYSTEM` and `PARSING_DESCRIPTION` message kinds, append the message content to `system_messages` if it exists.
    - For `ASSISTANT` and `TOOL_CALL_REQUEST` message kinds, create a dictionary with role 'assistant' and append it to `messages`.
    - For `USER`, `DEVELOPER`, `TOOL_CALL_RESPONSE`, and `ITERATION` message kinds, create a dictionary with role 'user' and append it to `messages`.
    - Combine all `system_messages` into a single string separated by double newlines, or set to `None` if no system messages exist.
    - Return a tuple containing the `messages` list and the combined system message content.
- **Output**:
    - A tuple containing a list of regular messages formatted for Anthropic and a combined system message string or `None` if no system messages exist.


---
#### LlmMessageHistory.to_openai_o1
The `to_openai_o1` function converts a message history into a list of OpenAI-compatible message parameter objects for a specific API variant called 'O1', mapping different message kinds to user or assistant roles.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty list `messages` to store the converted message objects.
    - Iterate over each message in `self.messages`.
    - Use a match-case statement to determine the `message_kind` of each message.
    - For `TOOL_CALL_RESPONSE`, `SYSTEM`, `DEVELOPER`, `USER`, `PARSING_DESCRIPTION`, and `ITERATION` message kinds, create a `ChatCompletionUserMessageParam` with role 'user' and the message's content.
    - For `ASSISTANT` message kind, create a `ChatCompletionAssistantMessageParam` with role 'assistant', the message's content, and any associated `tool_calls`.
    - For `TOOL_CALL_REQUEST` message kind, create a `ChatCompletionAssistantMessageParam` with role 'assistant' and the message's content.
    - Append the created message dictionary to the `messages` list.
    - Return the `messages` list.
- **Output**:
    - A list of dictionaries, each representing a message with 'role' and 'content' fields, and optionally 'tool_calls' for assistant messages.


---
#### LlmMessageHistory.to_openai_o3
The `to_openai_o3` function converts a sequence of LlmMessage objects into a list of OpenAI-compatible message parameter objects for a specific API variant called 'O3'.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty list `messages` to store the converted message parameter objects.
    - Iterate over each `message` in `self.messages`.
    - Use a match statement to determine the `message_kind` of each `message`.
    - For each `message_kind`, create a corresponding message parameter object with appropriate role and content fields.
    - Append the created message parameter object to the `messages` list.
    - Return the `messages` list containing all the converted message parameter objects.
- **Output**:
    - A list of OpenAI-compatible message parameter objects, each containing role and content fields, and optionally tool_calls when relevant.


---
#### LlmMessageHistory.to_openai_strict
The `to_openai_strict` function converts a list of `LlmMessage` objects into a list of `ChatCompletionMessageParam` objects suitable for OpenAI's strict API.
- **Inputs**:
    - `self`: An instance of the `LlmMessageHistory` class containing a list of `LlmMessage` objects.
- **Control Flow**:
    - Initialize an empty list `messages` to store the converted message parameters.
    - Iterate over each `message` in `self.messages`.
    - Use a `match` statement to determine the `message_kind` of each `message`.
    - For each `message_kind`, create an appropriate `ChatCompletionMessageParam` object with the necessary fields populated.
    - Append the created `ChatCompletionMessageParam` object to the `messages` list.
    - Return the `messages` list containing all converted message parameters.
- **Output**:
    - A list of `ChatCompletionMessageParam` objects, each representing a converted message from the original `LlmMessage` objects, formatted for OpenAI's strict API.



