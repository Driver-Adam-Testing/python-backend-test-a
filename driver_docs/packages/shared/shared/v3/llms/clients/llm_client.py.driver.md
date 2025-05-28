# Purpose
The provided Python code defines an abstract base class `LlmClient` that serves as a foundational component for creating clients that interact with various language model APIs. This file is part of a larger system designed to handle different configurations and types of language model interactions, as indicated by the imports from shared interfaces and configuration modules. The `LlmClient` class is designed to be subclassed, with specific implementations provided for different API kinds, such as OpenAI and Claude, as determined by the `from_config` class method. This method dynamically imports and returns the appropriate subclass based on the configuration provided, which is encapsulated in the `LlmConfig` object.

The class provides several methods for generating responses from language models, both synchronously and asynchronously, and supports single-shot and multi-shot interactions. The `single_shot` and `multi_shot` methods allow for generating responses with or without tool calls, while their asynchronous counterparts, `single_shot_stream` and `multi_shot_stream`, yield responses in a streaming fashion. The abstract method `_generate` is intended to be implemented by subclasses to define the specific logic for generating responses, ensuring that the base class remains flexible and adaptable to different language model APIs. The code is structured to facilitate extensibility and integration with various language model configurations, making it a critical component of a broader language model management system.
# Imports and Dependencies

---
- `abc`
- `collections.abc`
- `shared.v3.globals.iteration_messages`
- `shared.v3.interfaces.llm_message`
- `shared.v3.interfaces.llm_message_history`
- `shared.v3.interfaces.llm_response_type`
- `shared.v3.interfaces.llm_stream_response`
- `shared.v3.interfaces.llm_tool`
- `shared.v3.llms.config.llm_config`
- `shared.v3.utils.datasource`
- `shared.v3.llms.clients.llm_client_openai_strict`
- `shared.v3.llms.clients.llm_client_openai_o1`
- `shared.v3.llms.clients.llm_client_openai_chat`
- `shared.v3.llms.clients.llm_client_claude`


# Classes

---
### LlmClient 
- **Type**: `class`
- **Members**:
    - `config`: Stores the configuration details for the LlmClient.
- **Description**: The `LlmClient` class is an abstract base class designed to interface with different language model clients based on a given configuration. It provides a mechanism to select the appropriate subclass of `LlmClient` through the `from_config` method, which matches the configuration's API kind to a specific client implementation. The class includes methods for generating responses from language models, both synchronously and asynchronously, with support for single and multi-shot interactions. It also defines an abstract `_generate` method that must be implemented by subclasses to handle the specifics of message generation. The class supports streaming responses and tool execution during multi-shot interactions, allowing for complex interaction patterns with language models.
- **Inherits From**:
    - ABC

**Methods**

---
#### LlmClient.__init__
The `__init__` function initializes an instance of the `LlmClient` class with a given configuration.
- **Inputs**:
    - `config`: An instance of `LlmConfig` containing configuration details for the `LlmClient`.
- **Control Flow**:
    - The function assigns the provided `config` parameter to the `config` attribute of the `LlmClient` instance.
- **Output**:
    - The function does not return any value; it initializes the instance with the provided configuration.


---
#### LlmClient._generate
The `_generate` function is an abstract method intended to generate a response from a language model using a given message history, response type, and tool types.
- **Inputs**:
    - `message_history`: An instance of `LlmMessageHistory` that contains the message history to be used for generating a response.
    - `response_type`: An optional type of `LlmResponseType` that specifies the response type to be used for generation.
    - `tool_types`: An optional list of types of `LlmTool` that specifies the tool types to be used for generation.
- **Control Flow**:
    - The function is defined as an abstract method, meaning it must be implemented by subclasses of the class in which it is defined.
    - The function raises a `NotImplementedError` to indicate that it is a placeholder and needs to be implemented by subclasses.
    - The function assumes that the `message_history` does not contain model-specific messages, which must be added in the subclass implementation.
    - The subclass implementation must ensure that the `message_history` is copied when appending model-specific messages to avoid mutation.
- **Output**:
    - The function does not return any value as it is intended to be implemented by subclasses, which will define the specific output behavior.


---
#### LlmClient._generate_stream
The `_generate_stream` function asynchronously generates a stream of messages by yielding the last message from a given message history.
- **Inputs**:
    - `message_history`: An instance of `LlmMessageHistory` that contains the history of messages to be used for generating the stream.
    - `response_type`: An optional type of `LlmResponseType` that specifies the type of response to generate.
    - `tool_types`: An optional list of `LlmTool` types that may be used during the generation process.
- **Control Flow**:
    - Call the `_generate` method with the provided `message_history`, `response_type`, and `tool_types` to perform any necessary message generation or processing.
    - Yield the last message from the `message_history` using `message_history.last()`.
- **Output**:
    - An asynchronous generator that yields the last message from the `message_history`, which can be an `LlmMessage` or a string.


---
#### LlmClient.claude_haiku_3_5
The `claude_haiku_3_5` function returns an instance of `LlmClient` configured for the Claude Haiku 3.5 model.
- **Inputs**:
    - `cls`: The class type from which the method is called, typically `LlmClient` or a subclass.
- **Control Flow**:
    - The function calls `LlmConfig.claude_haiku_3_5()` to obtain a configuration specific to the Claude Haiku 3.5 model.
    - It then calls the `from_config` class method with this configuration to create and return an appropriate `LlmClient` instance.
- **Output**:
    - An instance of `LlmClient` configured for the Claude Haiku 3.5 model.


---
#### LlmClient.claude_sonnet_3_5
The `claude_sonnet_3_5` function returns an instance of an `LlmClient` subclass configured for the Claude Sonnet 3.5 API.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method of `LlmClient`.
    - It calls the `from_config` class method with a configuration specific to Claude Sonnet 3.5, obtained from `LlmConfig.claude_sonnet_3_5()`.
    - The `from_config` method determines the appropriate subclass of `LlmClient` to instantiate based on the API kind specified in the configuration.
- **Output**:
    - An instance of a subclass of `LlmClient` configured for the Claude Sonnet 3.5 API.


---
#### LlmClient.claude_sonnet_3_7
The `claude_sonnet_3_7` function returns an instance of an `LlmClient` subclass configured for the Claude Sonnet 3.7 API.
- **Inputs**:
    - `cls`: The class type that this class method is called on, typically a subclass of `LlmClient`.
- **Control Flow**:
    - The function calls `LlmConfig.claude_sonnet_3_7()` to obtain a configuration specific to the Claude Sonnet 3.7 API.
    - It then calls the `from_config` class method with this configuration to determine and return the appropriate `LlmClient` subclass instance.
- **Output**:
    - An instance of a subclass of `LlmClient` configured for the Claude Sonnet 3.7 API.


---
#### LlmClient.from_config
The `from_config` function selects and returns an appropriate subclass of `LlmClient` based on the provided `LlmConfig` configuration.
- **Inputs**:
    - `config`: An instance of `LlmConfig` that contains configuration details, including the API kind and provider.
- **Control Flow**:
    - The function uses a `match` statement to check the `api_kind` attribute of the `config` parameter.
    - If `api_kind` is `ApiKind.OPENAI_STRICT`, it imports and returns an instance of `OpenAiStrictWithSystemClient`.
    - If `api_kind` is `ApiKind.OPENAI_O1`, it imports and returns an instance of `OpenAiO1SeriesClient`.
    - If `api_kind` is `ApiKind.OPENAI_CHAT_WITH_TOOLS`, it imports and returns an instance of `OpenAiChatClient`.
    - If `api_kind` is `ApiKind.CLAUDE`, it imports and returns an instance of `ClaudeClient`.
    - If none of the cases match, it raises a `ValueError` indicating no suitable subclass was found for the given provider and API kind.
- **Output**:
    - An instance of a subclass of `LlmClient` that corresponds to the `api_kind` specified in the `config` parameter.


---
#### LlmClient.gpt_4_1
The `gpt_4_1` function returns an instance of a subclass of `LlmClient` configured for the GPT-4.1 model.
- **Inputs**:
    - `cls`: The class type that calls this class method, typically a subclass of `LlmClient`.
- **Control Flow**:
    - The function calls `cls.from_config` with a configuration specific to the GPT-4.1 model obtained from `LlmConfig.gpt_4_1()`.
    - The `from_config` method determines the appropriate subclass of `LlmClient` to instantiate based on the configuration's `api_kind`.
    - The function returns an instance of the determined subclass of `LlmClient`.
- **Output**:
    - An instance of a subclass of `LlmClient` configured for the GPT-4.1 model.


---
#### LlmClient.gpt_4_1_mini
The `gpt_4_1_mini` function returns an instance of `LlmClient` configured for the GPT-4.1 mini model.
- **Inputs**:
    - `cls`: The class type that this method is called on, typically a subclass of `LlmClient`.
- **Control Flow**:
    - Calls the `from_config` class method on `cls` with the configuration obtained from `LlmConfig.gpt_4_1_mini()`.
    - Returns the instance of `LlmClient` or its subclass configured for the GPT-4.1 mini model.
- **Output**:
    - An instance of `LlmClient` or its subclass configured with the GPT-4.1 mini model settings.


---
#### LlmClient.gpt_4_5
The `gpt_4_5` function returns an instance of an `LlmClient` subclass configured for the GPT-4.5 model.
- **Inputs**:
    - `cls`: The class type on which this class method is called, typically `LlmClient` or a subclass thereof.
- **Control Flow**:
    - The function calls `LlmConfig.gpt_4_5()` to obtain a configuration specific to the GPT-4.5 model.
    - It then calls the `from_config` class method with this configuration to determine and return the appropriate `LlmClient` subclass instance.
- **Output**:
    - An instance of a subclass of `LlmClient` configured for the GPT-4.5 model.


---
#### LlmClient.gpt_4o
The `gpt_4o` function returns an instance of `LlmClient` configured for the GPT-4o model.
- **Inputs**:
    - `cls`: The class `LlmClient` or its subclass from which the method is called.
- **Control Flow**:
    - The function calls `LlmConfig.gpt_4o()` to obtain a configuration specific to the GPT-4o model.
    - It then calls the `from_config` class method with this configuration to create and return an appropriate `LlmClient` instance.
- **Output**:
    - An instance of `LlmClient` configured for the GPT-4o model.


---
#### LlmClient.gpt_4o_chat
The `gpt_4o_chat` function returns an instance of an LlmClient subclass configured for GPT-4o chat.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method of the LlmClient class.
    - It calls the `from_config` class method with a configuration specific to GPT-4o chat, obtained from `LlmConfig.gpt_4o_chat()`.
    - The `from_config` method determines the appropriate subclass of LlmClient to instantiate based on the configuration's API kind.
- **Output**:
    - An instance of a subclass of LlmClient configured for GPT-4o chat.


---
#### LlmClient.gpt_4o_mini
The `gpt_4o_mini` function returns an instance of `LlmClient` configured with the `gpt_4o_mini` configuration.
- **Inputs**:
    - `cls`: The class reference to `LlmClient` or its subclass, used to call the class method.
- **Control Flow**:
    - The function calls `cls.from_config` with `LlmConfig.gpt_4o_mini()` as the argument.
    - `LlmConfig.gpt_4o_mini()` presumably returns a configuration object specific to the 'gpt_4o_mini' setup.
    - `cls.from_config` determines the appropriate subclass of `LlmClient` to instantiate based on the provided configuration.
- **Output**:
    - An instance of a subclass of `LlmClient` configured with the 'gpt_4o_mini' settings.


---
#### LlmClient.gpt_4o_mini_chat
The `gpt_4o_mini_chat` function returns an instance of an LlmClient subclass configured for the GPT-4o mini chat model.
- **Inputs**:
    - `cls`: The class object of LlmClient or its subclass, used to call the class method.
- **Control Flow**:
    - The function calls `LlmConfig.gpt_4o_mini_chat()` to obtain a configuration specific to the GPT-4o mini chat model.
    - It then calls the `from_config` class method with this configuration to determine and return the appropriate LlmClient subclass instance.
- **Output**:
    - An instance of a subclass of LlmClient configured for the GPT-4o mini chat model.


---
#### LlmClient.multi_shot
The `multi_shot` function generates a response from a language model with multiple iterations, allowing for tool calls and returning the final message and list of tools used.
- **Inputs**:
    - `prompt`: A string representing the initial user prompt for the language model, or None if no prompt is provided.
    - `iterations`: An integer specifying the number of iterations to perform for generating the response.
    - `response_type`: The type of response expected from the language model, or None if not specified.
    - `tool_types`: A list of tool types that can be used during the response generation, or None if no tools are specified.
    - `message_history`: An instance of LlmMessageHistory to track the conversation history, or None to start with a new history.
    - `datasource`: An instance of DataSource to be used by tools during execution, or None if not applicable.
- **Control Flow**:
    - Initialize an empty list `called_tools` to keep track of tools used.
    - If `message_history` is None, initialize it as a new LlmMessageHistory instance.
    - Add a MultiShotIterationContextMessage to the message history.
    - If a `prompt` is provided, add it as a user message to the message history.
    - Iterate over the range of `iterations`, adding an IterationMessage for each iteration to the message history.
    - Call the `_generate` method to generate a response, passing the message history, response type, and tool types (except in the last iteration).
    - Check if the last message in the history is a TOOL_CALL_REQUEST; if so, execute each tool call and add the tool's response to the message history.
    - Break the loop if the last message is not a TOOL_CALL_REQUEST.
    - Return the last message in the message history and the list of called tools.
- **Output**:
    - A tuple containing the last LlmMessage generated and a list of LlmTool instances that were called during the process.


---
#### LlmClient.multi_shot_stream
The `multi_shot_stream` function asynchronously generates and streams responses from a language model over multiple iterations, handling tool calls and yielding various response types.
- **Inputs**:
    - `prompt`: An optional string input that serves as the initial user prompt for the language model.
    - `iterations`: An integer specifying the number of iterations to perform, defaulting to 2.
    - `response_type`: An optional type of `LlmResponseType` that specifies the desired response format.
    - `tool_types`: An optional list of `LlmTool` types that can be used during the response generation, applicable for all but the last iteration.
    - `message_history`: An optional `LlmMessageHistory` object that maintains the history of messages exchanged with the language model.
    - `datasource`: An optional `DataSource` object used for executing tool calls.
- **Control Flow**:
    - Initialize an empty list `called_tools` to keep track of tools called during execution.
    - If `message_history` is not provided, initialize it as a new `LlmMessageHistory` object.
    - Add a `MultiShotIterationContextMessage` to the `message_history`.
    - If a `prompt` is provided, add it as a `USER` message to the `message_history`.
    - Set `should_continue` to `True` to control the iteration loop.
    - For each iteration up to the specified `iterations`, check if `should_continue` is `False` to break the loop early.
    - Add an `IterationMessage` to the `message_history` for the current iteration.
    - Call `_generate_stream` to get a response stream for the current iteration.
    - For each `chunk` in the `response_stream`, handle it based on its type:
    - If `chunk` is an `LlmMessage` with `TOOL_CALL_REQUEST`, execute the tool and yield `ToolStatusUpdateStreamResponse` before and after execution.
    - If `chunk` is a `str`, yield it as a `ResponseChunkStreamResponse` and set `should_continue` to `False`.
    - If `chunk` is a completed `LlmMessage`, yield it as a `ResponseFullStreamResponse` and set `should_continue` to `False`.
    - If `chunk` is of an unexpected type, yield an `ErrorStreamResponse` and raise a `ValueError`.
- **Output**:
    - An asynchronous generator yielding `LlmStreamResponse` objects, which can be of various types such as `ToolStatusUpdateStreamResponse`, `ResponseChunkStreamResponse`, `ResponseFullStreamResponse`, or `ErrorStreamResponse`.


---
#### LlmClient.o1
The `o1` function returns an instance of an `LlmClient` subclass configured with the `o1` configuration.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `LlmConfig.o1()` to obtain a specific configuration for the LLM client.
    - It then calls `cls.from_config()` with this configuration to determine and return the appropriate subclass of `LlmClient`.
- **Output**:
    - An instance of a subclass of `LlmClient` configured with the `o1` configuration.


---
#### LlmClient.o1_mini
The `o1_mini` function returns an instance of `LlmClient` configured with the `o1_mini` configuration.
- **Inputs**:
    - `cls`: The class `LlmClient` or a subclass from which the method is called.
- **Control Flow**:
    - The function calls `LlmConfig.o1_mini()` to obtain a specific configuration for the LLM client.
    - It then calls the `from_config` class method with this configuration to determine and return the appropriate subclass instance of `LlmClient`.
- **Output**:
    - An instance of a subclass of `LlmClient` configured with the `o1_mini` configuration.


---
#### LlmClient.o3_mini
The `o3_mini` function returns an instance of `LlmClient` configured with the `o3_mini` configuration.
- **Inputs**:
    - `cls`: The class `LlmClient` or a subclass from which the method is called.
- **Control Flow**:
    - The function calls `LlmConfig.o3_mini()` to obtain a specific configuration for the LLM client.
    - It then calls the `from_config` class method with this configuration to create and return an instance of `LlmClient` or its appropriate subclass.
- **Output**:
    - An instance of `LlmClient` or its subclass, configured with the `o3_mini` configuration.


---
#### LlmClient.o4_mini
The `o4_mini` function returns an instance of a subclass of `LlmClient` configured with the `o4_mini` configuration.
- **Inputs**:
    - `cls`: The class `LlmClient` or a subclass thereof, from which the method is called.
- **Control Flow**:
    - The function calls `LlmConfig.o4_mini()` to obtain a specific configuration for the LLM client.
    - It then calls the `from_config` class method with this configuration to determine and return the appropriate subclass of `LlmClient`.
- **Output**:
    - An instance of a subclass of `LlmClient` configured with the `o4_mini` configuration.


---
#### LlmClient.single_shot
The `single_shot` function generates a single response from a language model using a given prompt and message history.
- **Inputs**:
    - `prompt`: A string representing the prompt to use for generating the response, or None if no prompt is provided.
    - `response_type`: A type of `LlmResponseType` indicating the desired response type for the generation, or None if not specified.
    - `message_history`: An instance of `LlmMessageHistory` containing the message history to use for the generation, or None if no history is provided.
- **Control Flow**:
    - Check if `message_history` is None; if so, initialize it as an empty `LlmMessageHistory` object.
    - If a `prompt` is provided, add it as a user message to the `message_history`.
    - Call the `_generate` method with the `message_history`, `response_type`, and `tool_types` set to None to generate a response.
    - Return the last message from the `message_history` as the generated response.
- **Output**:
    - The function returns an `LlmMessage` object representing the generated response from the language model.


---
#### LlmClient.single_shot_stream
The `single_shot_stream` function asynchronously generates a stream of responses from a language model based on a given prompt and message history.
- **Inputs**:
    - `prompt`: An optional string representing the initial prompt to use for generating the response.
    - `response_type`: An optional type of `LlmResponseType` that specifies the type of response expected from the language model.
    - `message_history`: An optional `LlmMessageHistory` object that contains the history of messages to be used for generating the response.
- **Control Flow**:
    - The function calls `_generate_stream` with the provided `message_history`, `response_type`, and `None` for `tool_types` to get an asynchronous generator `response_stream`.
    - It iterates asynchronously over each `chunk` in `response_stream`.
    - If `chunk` is an instance of `LlmMessage`, it yields a `ResponseFullStreamResponse` with the content of the `chunk`.
    - If `chunk` is not an instance of `LlmMessage`, it yields the `chunk` as is.
- **Output**:
    - An asynchronous generator that yields `LlmStreamResponse` objects, which can be either `ResponseFullStreamResponse` or other types of stream responses.



