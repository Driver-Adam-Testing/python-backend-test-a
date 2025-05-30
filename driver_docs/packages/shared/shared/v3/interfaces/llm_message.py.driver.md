# Purpose
This Python code defines a class `LlmMessage` using the Pydantic library, which is designed to handle and process messages in the context of a language model interface. The class is structured to manage different types of messages, particularly those involving tool call requests and responses, which are common in systems that integrate with language models like OpenAI's GPT or Anthropic's Claude. The `LlmMessage` class includes nested classes `ToolCallRequest` and `ToolCallResponse` to encapsulate the details of tool interactions, such as the tool's name, ID, and arguments. The class provides several class methods to create `LlmMessage` instances from various message formats, including OpenAI chat completion messages, strings, and Anthropic messages. These methods parse the message content, identify tool requests, and determine the message kind, which can be a tool call request, assistant message, or other types defined in the `MessageKind` enumeration.

The code is intended to be part of a larger system that processes and interprets messages from language models, likely serving as a library module rather than a standalone script. It provides a structured way to convert raw message data into a more manageable format, facilitating further processing or interaction with other components of the system. The `LlmMessage` class also includes utility methods like `print_to_console` for displaying message details in a color-coded format, and a custom `__hash__` method to enable the use of `LlmMessage` instances in hash-based collections. The code is modular and extensible, allowing for integration with various tool types and response formats, which is crucial for systems that need to handle diverse and dynamic interactions with language models.
# Imports and Dependencies

---
- `json`
- `typing.TYPE_CHECKING`
- `typing.Optional`
- `anthropic.types.Message`
- `anthropic.types.MessageParam`
- `openai.types.chat.ChatCompletionMessage`
- `openai.types.chat.ParsedChatCompletionMessage`
- `pydantic.BaseModel`
- `shared.v3.globals.constants.PARSEABLE_CLASS_NAME`
- `shared.v3.interfaces.llm_message_kind.MessageKind`
- `shared.v3.utils.parse_response_string.parse_response_string`


# Global Variables

---
### content 
- **Type**: `str | None`
- **Description**: The `content` variable is a global attribute of the `LlmMessage` class, defined as a string or None. It holds the main textual content of a message, which can be derived from various sources such as OpenAI or Anthropic message responses.
- **Use**: This variable is used to store and access the primary text content of an LlmMessage instance.


---
### parsed_content 
- **Type**: `BaseModel | None`
- **Description**: The `parsed_content` variable is an optional attribute of the `LlmMessage` class, which is intended to store a parsed representation of the message content. It is defined as a Pydantic `BaseModel` or `None`, allowing it to hold structured data if available.
- **Use**: This variable is used to store the parsed version of the message content, which can be utilized for further processing or analysis.


---
### parsed_tool 
- **Type**: `BaseModel | None`
- **Description**: The `parsed_tool` variable is a field within the `ToolCallRequest` class, which is a nested class inside the `LlmMessage` class. It is defined as a type that can either be a `BaseModel` instance or `None`. This variable is intended to store a parsed representation of a tool's arguments, which are expected to be in a structured format that can be represented by a Pydantic `BaseModel`.
- **Use**: This variable is used to hold the parsed arguments of a tool call, allowing for structured data handling within the `ToolCallRequest` instances.


---
### tool_requests 
- **Type**: `list[LlmMessage.ToolCallRequest]`
- **Description**: The `tool_requests` variable is a list that stores instances of the `ToolCallRequest` class, which is defined within the `LlmMessage` class. Each `ToolCallRequest` instance represents a request to call a specific tool, containing details such as the tool's ID, name, arguments, and optionally parsed tool data.
- **Use**: This variable is used to keep track of all tool call requests associated with a particular `LlmMessage` instance, allowing the system to manage and execute these requests as needed.


---
### tool_response 
- **Type**: `ToolCallResponse | None`
- **Description**: The `tool_response` variable is an instance of the `ToolCallResponse` class or `None`. It is part of the `LlmMessage` class and is used to store the response from a tool call, including the tool's name and an optional identifier.
- **Use**: This variable is used to hold the response data from a tool call within an `LlmMessage` instance, allowing for the tracking and handling of tool call responses.


# Classes

---
### LlmMessage 
- **Type**: `class`
- **Members**:
    - `ToolCallRequest`: A nested class representing a request to call a tool with specific arguments.
    - `ToolCallResponse`: A nested class representing the response from a tool call.
    - `message_kind`: Indicates the type of message, such as user, assistant, or tool call request.
    - `content`: Holds the main content of the message, which can be None.
    - `parsed_content`: Stores the parsed content of the message, if available.
    - `tool_response`: Contains the response from a tool call, if applicable.
    - `tool_requests`: A list of tool call requests associated with the message.
    - `persist`: A property that determines if the message should be persisted based on its kind.
- **Description**: The `LlmMessage` class is a comprehensive model for handling messages in a large language model (LLM) context, particularly focusing on interactions involving tool calls. It extends the `BaseModel` from Pydantic and includes nested classes for tool call requests and responses. The class provides several class methods to create instances from different types of messages, such as those from OpenAI or Anthropic, and includes functionality to parse message content, manage tool requests, and determine message persistence. Additionally, it offers a method to print the message details to the console with color-coded output based on the message kind.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### LlmMessage.__hash__
The `__hash__` function generates a hash value for an `LlmMessage` instance based on its message kind, content, and tool requests.
- **Inputs**:
    - None
- **Control Flow**:
    - The function converts the `message_kind`, `content`, and a list of tuples containing `name`, `arguments`, and `id` from each `ToolCallRequest` in `tool_requests` into a string representation.
    - It then computes the hash of this string using Python's built-in `hash` function.
    - Finally, it returns the computed hash value.
- **Output**:
    - An integer representing the hash value of the `LlmMessage` instance.


---
#### LlmMessage.from_anthropic_message
The `from_anthropic_message` function creates an `LlmMessage` instance from an Anthropic message response, optionally parsing it into tool requests or a specific response type.
- **Inputs**:
    - `message`: The Anthropic message response, which can be of type `Message` or `MessageParam`.
    - `tool_types`: An optional list of tool types (`LlmTool`) that can be used to parse tool responses.
    - `response_type`: An optional type (`LlmResponseType`) to parse the response content into.
- **Control Flow**:
    - Initialize `content` as an empty string.
    - Check if `message` is an instance of `Message` and extract the first text content if available; otherwise, if it's a `MessageParam`, directly assign its content.
    - Attempt to parse `content` into JSON using `parse_response_string`; handle exceptions by setting `content_as_json` to `None`.
    - Initialize an empty list `tool_requests`.
    - If `tool_types` and `content_as_json` are available, iterate over `content_as_json` to find and instantiate tools matching the class name in `content_json`, appending them to `tool_requests`.
    - If `response_type` is provided and no `tool_requests` exist, attempt to parse `content_as_json` into `parsed_content` using `response_type`; handle exceptions by setting `parsed_content` to `None`.
    - Determine `message_kind` as `MessageKind.TOOL_CALL_REQUEST` if `tool_requests` exist, otherwise set it to `MessageKind.ASSISTANT`.
    - Return a new `LlmMessage` instance with the determined `message_kind`, `content`, `tool_requests`, and `parsed_content`.
- **Output**:
    - An `LlmMessage` instance containing the message content, any parsed tool requests, and optionally parsed content.


---
#### LlmMessage.from_openai_chat_completion_message
The function `from_openai_chat_completion_message` creates an `LlmMessage` instance from an OpenAI chat completion message, parsing its content and tool calls to determine the message kind and any tool requests or parsed content.
- **Inputs**:
    - `cls`: The class reference to `LlmMessage`, used to create an instance of it.
    - `chat_message`: An instance of `ChatCompletionMessage` containing the content and tool calls to be processed.
    - `tool_types`: An optional list of `LlmTool` types that can be used to parse tool requests from the message.
    - `response_type`: An optional `LlmResponseType` used to parse the response content if no tool requests are present.
- **Control Flow**:
    - Attempt to parse the `chat_message.content` into JSON using `parse_response_string`; if it fails, set `content_as_json` to `None`.
    - Initialize an empty list `tool_requests` to store any tool call requests extracted from the message.
    - If `chat_message.tool_calls` is present, iterate over each tool call to create `ToolCallRequest` instances, attempting to match and instantiate tools from `tool_types` based on the tool call's function name.
    - If no tool calls are present but `chat_message.content` is available and parsed successfully, check if the content contains a parseable class name and attempt to create tool requests using `tool_types`.
    - If a `response_type` is provided and no tool requests are found, attempt to parse the first item in `content_as_json` into `parsed_content` using `response_type`.
    - Determine the `message_kind` as `TOOL_CALL_REQUEST` if tool requests exist, otherwise set it to `ASSISTANT`.
    - Return a new `LlmMessage` instance with the determined `message_kind`, original content, any tool requests, and parsed content.
- **Output**:
    - An `LlmMessage` instance with the message kind, content, tool requests, and parsed content based on the input `chat_message` and optional parameters.


---
#### LlmMessage.from_openai_parsed_chat_completion_message
The function `from_openai_parsed_chat_completion_message` creates an `LlmMessage` instance from a `ParsedChatCompletionMessage` by extracting tool call requests and determining the message kind.
- **Inputs**:
    - `cls`: The class `LlmMessage` itself, used to create an instance of the class.
    - `parsed_message`: An instance of `ParsedChatCompletionMessage` containing parsed data from an OpenAI chat completion message.
- **Control Flow**:
    - Check if `parsed_message` contains any tool calls.
    - If tool calls exist, create a list of `ToolCallRequest` instances from each tool call in `parsed_message`.
    - Determine the `message_kind` as `TOOL_CALL_REQUEST` if there are tool requests, otherwise set it to `ASSISTANT`.
    - Return a new `LlmMessage` instance with the determined `message_kind`, the content from `parsed_message`, the list of tool requests, and the parsed content from `parsed_message`.
- **Output**:
    - An `LlmMessage` instance initialized with the message kind, content, tool requests, and parsed content derived from the `ParsedChatCompletionMessage`.


---
#### LlmMessage.from_string
The `from_string` function creates an `LlmMessage` instance from a string input, optionally parsing it into tool requests or a specific response type.
- **Inputs**:
    - `cls`: The class reference to `LlmMessage`, used to create an instance of it.
    - `string`: A string input that potentially contains JSON data to be parsed into tool requests or a response type.
    - `tool_types`: An optional list of `LlmTool` classes that can be used to parse tool requests from the string.
    - `response_type`: An optional `LlmResponseType` class used to parse the content into a specific response type if no tool requests are found.
- **Control Flow**:
    - Attempt to parse the input string into JSON using `parse_response_string`; if parsing fails, set `content_as_json` to None.
    - If `content_as_json` is a dictionary, convert it to a list containing that dictionary.
    - Initialize an empty list `tool_requests` to store any tool requests parsed from the JSON content.
    - Iterate over each JSON object in `content_as_json`; if it contains a `PARSEABLE_CLASS_NAME`, check against `tool_types` to find a matching tool class.
    - If a matching tool class is found, create a `ToolCallRequest` and append it to `tool_requests`.
    - If `tool_requests` is not empty, return an `LlmMessage` instance with `message_kind` set to `TOOL_CALL_REQUEST` and the `tool_requests` list.
    - If `response_type` is provided and `content_as_json` is not empty, attempt to parse the first JSON object into `parsed_content` using `response_type`.
    - Return an `LlmMessage` instance with `message_kind` set to `ASSISTANT`, the original string as `content`, and `parsed_content` if available.
- **Output**:
    - An `LlmMessage` instance with `message_kind` set to either `TOOL_CALL_REQUEST` or `ASSISTANT`, containing any parsed tool requests or response content.


---
#### LlmMessage.persist
The `persist` function determines if a message should be persisted based on its kind.
- **Inputs**:
    - None
- **Control Flow**:
    - The function checks if the `message_kind` attribute of the instance is not in a predefined list containing `MessageKind.ITERATION` and `MessageKind.PARSING_DESCRIPTION`.
    - If the `message_kind` is not in this list, the function returns `True`, indicating the message should be persisted.
    - If the `message_kind` is in the list, the function returns `False`, indicating the message should not be persisted.
- **Output**:
    - A boolean value indicating whether the message should be persisted or not.


---
#### LlmMessage.print_to_console
The `print_to_console` function prints the details of an LlmMessage instance to the console with color-coded formatting based on the message kind.
- **Inputs**:
    - None
- **Control Flow**:
    - A dictionary `color_map` is defined to map different `MessageKind` values to specific ANSI color codes for console output.
    - The `color_reset` variable is set to the ANSI code for resetting the console color.
    - The `message_color` is determined by looking up the `self.message_kind` in the `color_map`, with a default color if not found.
    - The message kind is printed to the console with the determined color.
    - If `self.tool_response` is not None, it prints the tool response details.
    - If `self.content` is not None, it prints the content of the message.
    - If `self.tool_requests` is not empty, it iterates over each tool request and prints its details (id, name, and arguments).
    - If `self.parsed_content` is not None, it prints the parsed content using the `model_dump` method.
    - Finally, it prints the `color_reset` to reset the console color.
- **Output**:
    - The function outputs the message details to the console, formatted with colors based on the message kind, and includes any tool responses, content, tool requests, and parsed content if they exist.


**Nested Classes**
    - ToolCallRequest
    - ToolCallResponse


---
### ToolCallRequest 
- **Type**: `class`
- **Members**:
    - `id`: A string representing the unique identifier for the tool call request.
    - `name`: A string representing the name of the tool being called.
    - `arguments`: A string containing the arguments for the tool call.
    - `parsed_tool`: An optional BaseModel instance representing the parsed tool, if available.
- **Description**: The `ToolCallRequest` class is a data model that represents a request to call a tool within a larger system. It includes attributes for identifying the request (`id`), specifying the tool to be called (`name`), providing the necessary arguments for the tool (`arguments`), and optionally storing a parsed representation of the tool (`parsed_tool`). This class is used to encapsulate the details of a tool call request, facilitating the management and processing of such requests within the system.
- **Inherits From**:
    - BaseModel


---
### ToolCallResponse 
- **Type**: `class`
- **Members**:
    - `name`: The name of the tool call response.
    - `id`: The identifier of the tool call response, which can be None.
- **Description**: The `ToolCallResponse` class is a simple data model that represents the response from a tool call, containing a name and an optional identifier. It is designed to be used within the context of handling tool call requests and responses, potentially allowing for future expansion to include executed tool references or message history parsing.
- **Inherits From**:
    - BaseModel


