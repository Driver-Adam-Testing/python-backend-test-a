# Purpose
This Python code file is designed to manage and track usage sessions for a language model, specifically integrating with AWS services and OpenAI's API. The primary functionality is encapsulated within the `LLMUsageSession` class, which handles the lifecycle of a usage session, including starting and ending sessions, sending usage events to an AWS EventBridge, and computing usage metrics. The class is structured to be used as a context manager, ensuring that sessions are properly closed and their statuses updated in a database, which is managed using SQLAlchemy and SQLModel. The code also includes error handling for event sending through a custom exception, `UsageEventSendError`.

The file imports several external libraries and modules, indicating its reliance on AWS for event handling, OpenAI for generating responses, and a database for session management. The `LLMUsageSession` class is central to the file, providing methods to compute usage metrics, send events, and generate responses using OpenAI's language model. The code is structured to be part of a larger application, likely a backend service, where it serves as a utility for tracking and managing the usage of language model sessions. The presence of detailed methods for event handling and session management suggests that this code is intended to be integrated into a broader system that requires precise tracking of language model interactions and their associated metrics.
# Imports and Dependencies

---
- `inspect`
- `json`
- `dataclasses.dataclass`
- `datetime.UTC`
- `datetime.datetime`
- `typing.Self`
- `typing.TypeVar`
- `uuid.UUID`
- `boto3`
- `openai`
- `database.db.engine`
- `database.models_v1.UsageEventType`
- `database.models_v1.UsageSession`
- `database.models_v1.UsageSessionStatus`
- `sqlalchemy.orm.attributes.flag_modified`
- `sqlmodel.Session`
- `shared.agent.chat_openai.ChatOpenAI`
- `shared.agent.chat_openai.OutputConfig`
- `shared.interfaces.usage.event_metadata.UsageEventMetadata`
- `shared.interfaces.usage.event_metadata.UsageMetric`
- `shared.interfaces.usage.event_metadata.UsageSessionMetadata`
- `shared.usage.utils.bytes_to_sloc`


# Global Variables

---
### _LLMUsageSession 
- **Type**: `TypeVar`
- **Description**: _LLMUsageSession is a TypeVar that is bound to the LLMUsageSession class. This allows for type hinting and ensures that the variable is used in contexts where an instance of LLMUsageSession or its subclasses is expected.
- **Use**: This variable is used for type hinting within the LLMUsageSession class to ensure type safety and consistency.


---
### aws_client 
- **Type**: `boto3.client`
- **Description**: The `aws_client` is a global variable intended to hold an instance of a boto3 client configured to interact with AWS services, specifically the 'events' service in the 'us-east-1' region. It is initialized as `None` and is set to a boto3 client instance when the `get_aws_client` function is called for the first time.
- **Use**: This variable is used to send events to AWS EventBridge, facilitating communication with AWS services for event-driven architectures.


---
### client 
- **Type**: `ChatOpenAI`
- **Description**: The `client` variable is an instance of the `ChatOpenAI` class, which is used to interact with the OpenAI API for generating responses based on given prompts. It is initialized within the `LLMUsageSession` class if not already provided during the session's instantiation.
- **Use**: This variable is used to generate responses from the OpenAI API when the `generate_response` method is called within the `LLMUsageSession` class.


---
### events_sent 
- **Type**: `int`
- **Description**: The `events_sent` variable is an integer that tracks the number of events successfully sent by an instance of the `LLMUsageSession` class. It is initialized to zero and incremented each time an event is sent without error.
- **Use**: This variable is used to keep a count of the number of events sent during a session, which is then stored in the session metadata when the session ends.


---
### session_id 
- **Type**: `UUID | None`
- **Description**: The `session_id` is a global variable within the `LLMUsageSession` dataclass, representing the unique identifier for a usage session. It is of type `UUID` and can be `None` initially, indicating that a session has not yet been started.
- **Use**: This variable is used to uniquely identify and manage the lifecycle of a usage session within the `LLMUsageSession` class.


# Classes

---
### LLMUsageSession 
- **Type**: `dataclass`
- **Members**:
    - `organization_id`: A string representing the organization ID associated with the session.
    - `user_id`: A string representing the user ID associated with the session.
    - `session_metadata`: An instance of UsageSessionMetadata containing metadata for the session.
    - `session_id`: A UUID representing the session ID, which can be None initially.
    - `client`: An instance of ChatOpenAI used for generating responses, which can be None initially.
    - `events_sent`: An integer counting the number of events sent during the session.
    - `aws_client`: An instance of boto3.client for AWS interactions, which can be None initially.
- **Description**: The LLMUsageSession class is a dataclass designed to manage and track the usage of a language model session. It handles session lifecycle events such as starting and ending a session, sending usage metrics to an AWS event bus, and computing usage metrics based on prompts and responses. The class supports context management to ensure sessions are properly closed and provides methods to generate responses using a language model client, compute usage metrics, and send events to a metrics event bus. It integrates with a database to store session information and uses AWS services for event handling.

**Methods**

---
#### LLMUsageSession.__enter__
The `__enter__` function initializes and returns the current instance of the `LLMUsageSession` class when entering a context manager block.
- **Inputs**:
    - `self`: An instance of the `_LLMUsageSession` class, which is a type variable bound to `LLMUsageSession`.
- **Control Flow**:
    - The function is called when entering a context manager block using the `with` statement.
    - It simply returns the current instance of the `LLMUsageSession` class.
- **Output**:
    - The function returns the current instance of the `LLMUsageSession` class (`self`).


---
#### LLMUsageSession.__exit__
The `__exit__` function finalizes a usage session by setting its status based on whether an exception occurred during the session.
- **Inputs**:
    - `exc_type`: The type of exception that was raised, if any, during the session.
    - `exc_val`: The exception instance that was raised, if any, during the session.
    - `exc_tb`: The traceback object associated with the exception, if any, during the session.
- **Control Flow**:
    - Check if `exc_type` is `None` to determine if an exception occurred.
    - If `exc_type` is `None`, set the session status to `UsageSessionStatus.COMPLETED`.
    - If `exc_type` is not `None`, set the session status to `UsageSessionStatus.FAILED`.
    - Call the `_end_session` method with the determined status to finalize the session.
- **Output**:
    - The function does not return any value; it performs an action to end the session with a specific status.


---
#### LLMUsageSession.__post_init__
The `__post_init__` function initializes the session ID for an `LLMUsageSession` instance if it is not already set.
- **Inputs**:
    - `self`: An instance of the `LLMUsageSession` class.
- **Control Flow**:
    - Check if `self.session_id` is `None`.
    - If `self.session_id` is `None`, call the `_start_session` method to initialize `self.session_id`.
- **Output**:
    - The function does not return any value; it modifies the `session_id` attribute of the instance in place.


---
#### LLMUsageSession._end_session
The `_end_session` function finalizes a usage session by updating its status and metadata in the database.
- **Inputs**:
    - `status`: The new status of the session, which is an instance of `UsageSessionStatus`.
- **Control Flow**:
    - Open a new database session using `Session(engine)`.
    - Retrieve the `UsageSession` object from the database using the current `session_id`.
    - Update the `status` of the `UsageSession` object with the provided `status` argument.
    - Retrieve or initialize the `session_metadata` dictionary from the `UsageSession` object.
    - Update the `session_metadata` dictionary with the number of events sent (`self.events_sent`).
    - Mark the `session_metadata` field as modified using `flag_modified`.
    - Add the updated `UsageSession` object back to the session.
    - Commit the transaction to save changes to the database.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### LLMUsageSession._start_session
The `_start_session` function initializes a new usage session in the database and returns its unique identifier.
- **Inputs**:
    - `self`: An instance of the `LLMUsageSession` class, containing attributes like `organization_id`, `user_id`, and `session_metadata`.
- **Control Flow**:
    - A new database session is opened using the `Session` context manager with the `engine`.
    - A `UsageSession` object is created with the status set to `RUNNING`, and initialized with `organization_id`, `user_id`, and serialized `session_metadata` from the `self` instance.
    - The `UsageSession` object is added to the database session.
    - The database session is committed to save the new `UsageSession` to the database.
    - The `UsageSession` object is refreshed to update it with the latest data from the database, including its generated ID.
    - The function returns the `id` of the newly created `UsageSession`.
- **Output**:
    - The function returns a `UUID` representing the unique identifier of the newly created usage session.


---
#### LLMUsageSession.commit_event_now
The `commit_event_now` function converts a `UsageMetric` into a `UsageEvent` and commits it to the database.
- **Inputs**:
    - `usage_metric`: An instance of `UsageMetric` that contains the data to be converted and committed as a `UsageEvent`.
- **Control Flow**:
    - Convert the `usage_metric` into a `usage_event` using the `into_usage_event` method.
    - Open a new database session using `Session(engine)`.
    - Add the `usage_event` to the session.
    - Commit the session to save the `usage_event` to the database.
- **Output**:
    - The function does not return any value; it performs a database commit operation.


---
#### LLMUsageSession.compute_usage
The `compute_usage` function calculates and returns a `UsageMetric` object based on the input prompts and response from an OpenAI chat completion, including metadata about the event.
- **Inputs**:
    - `prompts`: A list of strings representing the input prompts to the OpenAI chat model.
    - `response`: An `openai.ChatCompletion` object containing the response from the OpenAI chat model.
    - `event_type`: A `UsageEventType` object indicating the type of usage event being recorded.
    - `model`: A string specifying the model used, defaulting to 'gpt-4o-2024-08-06'.
    - `provider`: A string specifying the provider of the model, defaulting to 'OpenAI'.
- **Control Flow**:
    - Calculate `bytes_in` by summing the UTF-8 encoded byte lengths of all non-empty prompts.
    - Extract the response message content from the first choice in the response object.
    - Calculate `bytes_out` as the UTF-8 encoded byte length of the response message, if it exists.
    - Retrieve `tokens_in` and `tokens_out` from the response's usage data.
    - Use the `inspect` module to extract function names from the call stack to construct the `event_source`.
    - Create a `UsageEventMetadata` object with model, provider, input prompts, output response, and source lines of code (SLOC) calculated from bytes.
    - Instantiate a `UsageMetric` object with session details, byte and token counts, timestamp, event type, and metadata.
    - Return the `UsageMetric` object.
- **Output**:
    - A `UsageMetric` object containing details about the usage event, including byte and token counts, event source, and metadata.


---
#### LLMUsageSession.generate_response
The `generate_response` function generates a response from a language model based on system and user prompts, logs usage metrics, and returns the generated message content.
- **Inputs**:
    - `system_prompt`: A string representing the system prompt to be used in generating the response.
    - `user_prompt`: A string representing the user prompt to be used in generating the response.
    - `output_cfg`: An instance of `OutputConfig` specifying the configuration for the output, with a default value of `OutputConfig.default()`.
    - `model`: A string specifying the model to be used, defaulting to 'gpt-4o-2024-08-06'.
    - `temperature`: An integer representing the temperature setting for the model, defaulting to 0.
    - `request_timeout`: An integer specifying the request timeout in seconds, defaulting to 300.
- **Control Flow**:
    - Check if the `client` attribute is `None`; if so, initialize it with a `ChatOpenAI` instance using the provided model, temperature, and request timeout.
    - Call the `generate_response` method on the `client` with the provided system and user prompts and output configuration to obtain a response.
    - Compute usage metrics by calling `compute_usage` with the prompts, response, and a specified event type.
    - Send the computed usage metrics by calling `send_event`.
    - Return the content of the first message choice from the response.
- **Output**:
    - The function returns a string containing the content of the generated message from the language model.


---
#### LLMUsageSession.send_event
The `send_event` function sends a usage metric event to an AWS EventBridge event bus and handles potential errors during the process.
- **Inputs**:
    - `usage_metric`: An instance of the UsageMetric class containing details about the usage event to be sent.
- **Control Flow**:
    - Check if an AWS client is provided; if not, obtain one using `get_aws_client`.
    - Create a copy of the `usage_metric` and convert it to a JSON string, adding an empty `event_metadata` field.
    - Construct an event entry dictionary with details such as time, source, detail type, detail, event bus name, and trace header.
    - Attempt to send the event using the AWS client's `put_events` method.
    - If successful, increment the `events_sent` counter and print a success message.
    - If an exception occurs, print an error message and raise a `UsageEventSendError` with the original exception.
- **Output**:
    - A dictionary containing the response from the AWS `put_events` call, or an exception is raised if an error occurs.



---
### UsageEventSendError 
- **Type**: `class`
- **Members**:
    - `original_exception`: Stores the original exception that caused the error, if any.
- **Description**: The `UsageEventSendError` class is a custom exception that inherits from Python's built-in `Exception` class. It is specifically designed to be raised when an error occurs during the process of sending a usage event. The class constructor allows for an optional message and an optional original exception to be passed, which can be useful for debugging and error handling purposes.
- **Inherits From**:
    - Exception

**Methods**

---
#### UsageEventSendError.__init__
The `__init__` function initializes a `UsageEventSendError` exception with a custom message and an optional original exception.
- **Inputs**:
    - `message`: A string representing the error message to be associated with the exception, defaulting to 'Error sending usage event'.
    - `original_exception`: An optional Exception object that represents the original exception that caused this error, defaulting to None.
- **Control Flow**:
    - The function calls the superclass's `__init__` method with the provided message to initialize the base Exception class.
    - It assigns the `original_exception` parameter to an instance variable `self.original_exception`.
- **Output**:
    - The function does not return any value as it is a constructor for initializing an exception object.



# Functions

---
### get_aws_client 
The `get_aws_client` function initializes and returns a global AWS client for interacting with AWS services, specifically the 'events' service in the 'us-east-1' region.
- **Inputs**:
    - None
- **Control Flow**:
    - Check if the global variable `aws_client` is `None`.
    - If `aws_client` is `None`, initialize it using `boto3.client` with the 'events' service and 'us-east-1' region.
    - Return the `aws_client`.
- **Output**:
    - The function returns a `boto3.client` object for the AWS 'events' service.


