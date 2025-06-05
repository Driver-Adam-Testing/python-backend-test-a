# Purpose
This Python code defines an abstract base class `AgentBase` that serves as a foundational component for creating agent-like entities capable of iterative processing and interaction. The class is designed to be extended by other classes that implement specific agent behaviors. It provides a structured framework for managing agent state, including model configuration, data scope, and logging capabilities. The class utilizes several external modules and libraries, such as `pydantic` for data validation, and integrates with a database to log agent instances and messages. The class is not a standalone script but rather a library component intended to be imported and extended by other modules.

The `AgentBase` class includes several key functionalities, such as managing agent messages, handling search results, and iterating through a defined number of processing steps. It uses abstract methods `_generate_response` and `_execute_iteration`, which must be implemented by subclasses to define specific agent behaviors. The class also supports logging and debugging, with options to store agent interactions in a database and print messages for debugging purposes. The `invoke` method orchestrates the agent's iterative process, handling prompts and responses, and ensuring that the agent operates within the specified iteration limits. This class is part of a broader system, as indicated by its imports from shared modules and its reliance on a database for logging, suggesting its role in a larger application architecture.
# Imports and Dependencies

---
- `json`
- `uuid`
- `abc`
- `database.db.get_session`
- `database.models_v1.RuntimeLogAgentInstance`
- `database.models_v1.RuntimeLogAgentMessage`
- `pydantic.BaseModel`
- `shared.agent.models.llm_models.ModelConfig`
- `shared.interfaces.agents.data_scope.DataScope`
- `shared.prompts.interface.iterations.PROMPT_FINAL_ITERATION`
- `shared.prompts.interface.iterations.PROMPT_FIRST_ITERATION`
- `shared.prompts.interface.iterations.PROMPT_MIDDLE_ITERATION`
- `shared.usage.llm_session.LLMUsageSession`
- `shared.utils.bcolors.print_dict`


# Classes

---
### AgentBase 
- **Type**: `class`
- **Members**:
    - `log`: Indicates whether logging is enabled for the agent.
    - `scope`: Defines the data scope within which the agent operates.
    - `model`: Specifies the model used by the agent.
    - `debug`: Indicates whether debug mode is enabled for the agent.
    - `agent_id`: Unique identifier for the agent instance.
    - `tools`: List of tools available to the agent.
    - `max_iterations`: Maximum number of iterations the agent can perform.
    - `iteration`: Current iteration count of the agent.
    - `messages`: List of messages processed by the agent.
    - `search_results`: Stores search results obtained by the agent.
    - `response_format`: Specifies the format for the agent's response.
    - `llm_usage_session`: Session information for LLM usage.
- **Description**: The `AgentBase` class is an abstract base class designed to serve as a foundation for creating agent instances that interact with models and perform iterative tasks. It manages the agent's configuration, including model selection, data scope, and available tools, while also handling logging and debugging functionalities. The class supports message handling and search result storage, and it enforces a structure for generating responses and executing iterations through abstract methods. The `invoke` method orchestrates the iterative process, ensuring that the agent operates within the specified iteration limits and logs interactions if enabled.
- **Inherits From**:
    - ABC

**Methods**

---
#### AgentBase.__init__
The `__init__` function initializes an instance of the `AgentBase` class with various configuration parameters and optionally retrieves or creates a logging agent instance.
- **Inputs**:
    - `model`: A string representing the model name to be used by the agent.
    - `scope`: An instance of `DataScope` that defines the data access scope for the agent.
    - `tools`: An optional list of tools (of any type) that the agent can use; defaults to an empty list if not provided.
    - `max_iterations`: An integer specifying the maximum number of iterations the agent can perform; defaults to 1.
    - `agent_id`: An optional UUID representing the unique identifier of an existing agent instance; if not provided, a new instance may be created.
    - `response_format`: An optional type that specifies the format of the response; defaults to None.
    - `log`: A boolean indicating whether logging is enabled; defaults to True.
    - `debug`: A boolean indicating whether debug mode is enabled; defaults to True.
    - `llm_usage_session`: An optional instance of `LLMUsageSession` for tracking usage; defaults to None.
- **Control Flow**:
    - Initialize instance variables with provided arguments or default values.
    - Check if `agent_id` is provided; if so, retrieve the corresponding agent instance from the database and add its messages to the current instance.
    - If `agent_id` is not provided and logging is enabled, create a new `RuntimeLogAgentInstance` in the database, commit the transaction, and set `agent_id` to the new instance's ID.
- **Output**:
    - The function does not return any value; it initializes the state of the `AgentBase` instance.


---
#### AgentBase._execute_iteration
The `_execute_iteration` function is an abstract method intended to be implemented by subclasses to perform a single iteration of an agent's task, returning a string or None.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is defined as an abstract method using the `@abstractmethod` decorator, indicating that it must be implemented by any subclass of `AgentBase`.
    - The function raises a `NotImplementedError`, which serves as a placeholder to enforce implementation in subclasses.
- **Output**:
    - The function is expected to return a string or None, but as an abstract method, it does not provide an actual implementation.


---
#### AgentBase._generate_response
The `_generate_response` function is an abstract method intended to be implemented by subclasses to generate a response based on provided completion arguments.
- **Inputs**:
    - `completion_kwargs`: A dictionary containing keyword arguments necessary for generating a response.
- **Control Flow**:
    - The function is defined as an abstract method, indicating that it must be implemented by any subclass of the class containing this method.
    - The function raises a `NotImplementedError`, which serves as a placeholder to enforce implementation in subclasses.
- **Output**:
    - The function is expected to return any type of response, as indicated by the return type `any`, but the actual output depends on the subclass implementation.


---
#### AgentBase._increment_iterator_message
The `_increment_iterator_message` function increments the iteration count and adds a message based on the current iteration status, returning whether further iterations are allowed.
- **Inputs**:
    - None
- **Control Flow**:
    - Increment the `iteration` attribute by 1.
    - Check if `max_iterations` is greater than 1.
    - If `iteration` is 1, add a message using `PROMPT_FIRST_ITERATION` with the remaining iterations.
    - If `iteration` is less than `max_iterations`, add a message using `PROMPT_MIDDLE_ITERATION` with the remaining iterations.
    - If `iteration` equals `max_iterations`, add a message using `PROMPT_FINAL_ITERATION`.
    - Return a boolean indicating if the current iteration is less than or equal to `max_iterations`.
- **Output**:
    - A boolean value indicating whether the current iteration is less than or equal to the maximum allowed iterations.


---
#### AgentBase._print_agent_message
The `_print_agent_message` function prints a given message using the `print_dict` utility.
- **Inputs**:
    - `message`: The message to be printed, which can be of any type.
- **Control Flow**:
    - The function takes a single argument `message`.
    - It calls the `print_dict` function with `message` as the argument to print it.
- **Output**:
    - The function does not return any value; it performs a side effect of printing the message.


---
#### AgentBase.add_message
The `add_message` function adds a message to the agent's message list, converting it to a dictionary format if necessary, and optionally prints the message if debugging is enabled.
- **Inputs**:
    - `message`: The message to be added, which can be of any type, but is expected to be either a string or an object with a `to_dict` method.
- **Control Flow**:
    - Check if the message is a string; if so, convert it to a dictionary with 'role' as 'user' and 'content' as the message string.
    - If the message has a `to_dict` method and it is callable, convert the message to a dictionary using this method.
    - Append the (possibly converted) message to the `messages` list of the agent.
    - If the `debug` attribute of the agent is `True`, call the `_print_agent_message` method to print the message.
- **Output**:
    - The function does not return any value; it modifies the agent's internal state by adding a message to its `messages` list.


---
#### AgentBase.add_search_results
The `add_search_results` function appends a given result to the `search_results` list of the class instance.
- **Inputs**:
    - `results`: The result to be added to the `search_results` list; it can be of any type.
- **Control Flow**:
    - The function takes a single argument `results`.
    - It appends the `results` to the `search_results` list attribute of the class instance.
- **Output**:
    - The function does not return any value; it modifies the `search_results` list in place.


---
#### AgentBase.invoke
The `invoke` function executes a series of iterations to generate a response based on a given prompt, logging messages and handling response formatting as needed.
- **Inputs**:
    - `prompt`: An optional string input representing the initial user prompt to be processed by the agent.
- **Control Flow**:
    - Initialize the iteration counter to zero.
    - If a prompt is provided, add it as a message with the role 'user'.
    - Enter a loop that continues as long as `_increment_iterator_message` returns True, indicating that the maximum number of iterations has not been exceeded.
    - Within the loop, call `_execute_iteration` to attempt generating a response.
    - If a response is generated, check if a response format is specified; if so, parse the response using the specified format, otherwise use the raw response.
    - If logging is enabled, log all messages to the database using a session context.
    - Return the final response if a valid response is generated within the allowed iterations.
    - If no valid response is generated after the maximum iterations, raise a `RuntimeError`.
- **Output**:
    - The function returns either a formatted response as a `BaseModel` instance or a raw string response, depending on the presence of a response format.


---
#### AgentBase.model_config
The `model_config` function retrieves a `ModelConfig` object based on the model name stored in the instance.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `ModelConfig.from_name` with `self.model` as the argument.
    - It returns the `ModelConfig` object obtained from the `from_name` method.
- **Output**:
    - A `ModelConfig` object corresponding to the model name stored in the instance.



