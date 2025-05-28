# Purpose
The provided code defines a configuration class for an "agent" using the Pydantic library, which is a data validation and settings management library in Python. The `AgentConfiguration` class is a model that specifies various attributes necessary for configuring an agent, such as the model to be used, system prompts, user prompts, the number of iterations, and tool configurations. This class is designed to be a part of a larger system where agents are configured and managed, likely in an AI or automation context. The class includes methods to retrieve tool functions from a tool registry and to format system prompts, indicating its role in preparing and managing the operational parameters of an agent.

The class is structured to be a part of a broader application, as evidenced by its imports from shared modules and its reliance on external components like `TOOL_REGISTRY` and `DataScope`. The `tools` property method dynamically retrieves tool instances based on the names provided in the configuration, ensuring that the agent can access the necessary functionalities. The `create_system_prompts` method formats system prompts into a specific structure, which suggests that the agent interacts with a system that requires prompts in a particular format. This code is likely intended to be imported and used within a larger application, serving as a configuration utility for setting up and managing agents with specific capabilities and behaviors.
# Imports and Dependencies

---
- `pydantic.BaseModel`
- `shared.agent.tools.TOOL_REGISTRY`
- `shared.interfaces.agents.data_scope.DataScope`


# Global Variables

---
### iterations 
- **Type**: `int`
- **Description**: The `iterations` variable is an integer that specifies the number of iterations the agent should perform. It is part of the `AgentConfiguration` class, which is used to configure various aspects of an agent, including its model, prompts, and tools.
- **Use**: This variable is used to determine how many times the agent should execute its main loop or task.


---
### model 
- **Type**: `str | None`
- **Description**: The `model` variable is a string or None, representing the model to be used by the agent. It is part of the `AgentConfiguration` class, which is a subclass of `BaseModel` from the Pydantic library. This variable allows the configuration of the agent to specify which model should be utilized during its operation.
- **Use**: The `model` variable is used to define the model that the agent will use, and it can be set to a specific model name or left as None if no model is specified.


---
### response_format 
- **Type**: `type | None`
- **Description**: The `response_format` variable is a type hint that indicates the expected format of the response from the agent. It is defined as a type or None, meaning it can either be a specific type or not set at all.
- **Use**: This variable is used to specify or determine the format in which the agent's response should be structured.


---
### scope 
- **Type**: `DataScope | None`
- **Description**: The `scope` variable is an attribute of the `AgentConfiguration` class, defined as an optional instance of the `DataScope` class. It is used to specify the data scope within which the agent operates, providing context or boundaries for data processing.
- **Use**: This variable is used to define the data scope for the agent, which can influence how the agent processes and interacts with data.


---
### system_prompts 
- **Type**: `list[str]`
- **Description**: The `system_prompts` variable is a list of strings that represent system prompts used by the agent. These prompts are intended to guide the behavior or responses of the agent during its operation.
- **Use**: This variable is used to store and manage the system prompts that are applied to the agent's configuration, influencing its interaction logic.


---
### tool_names 
- **Type**: `list[str]`
- **Description**: The `tool_names` variable is a list of strings that represents the names of tools configured for an agent. It is part of the `AgentConfiguration` class, which is a Pydantic model used to define the configuration settings for an agent. This list is used to map tool names to their corresponding classes in the `TOOL_REGISTRY`.
- **Use**: This variable is used to store the names of tools that the agent can utilize, which are later retrieved and instantiated from the `TOOL_REGISTRY`.


# Classes

---
### AgentConfiguration 
- **Type**: `class`
- **Members**:
    - `model`: The model to be used by the agent.
    - `system_prompts`: List of system prompts.
    - `iterations`: Number of iterations the agent should perform.
    - `tool_names`: List of tool names to be used by the agent.
    - `scope`: The data scope for the agent.
    - `response_format`: The format of the response expected from the agent.
- **Description**: The `AgentConfiguration` class is a configuration model for an agent, inheriting from `BaseModel`. It defines various attributes such as the model, system prompts, iterations, tool names, scope, and response format, which are essential for configuring the behavior and capabilities of an agent. The class provides a property `tools` to retrieve tool instances based on the tool names specified, and a method `create_system_prompts` to format system prompts into a required structure. This class is crucial for setting up and managing the configuration of agents in a structured and flexible manner.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### AgentConfiguration.create_system_prompts
The `create_system_prompts` function formats a list of system prompts into a specific dictionary format by resolving module attributes or defaulting to a basic structure.
- **Inputs**:
    - `self`: An instance of the class containing the `system_prompts` attribute, which is a list of strings representing system prompts.
- **Control Flow**:
    - Import the `prompts` module from the `shared` package.
    - Initialize an empty list `formatted_prompts` to store the formatted prompts.
    - Check if `self.system_prompts` is not empty.
    - Iterate over each `system_prompt` in `self.system_prompts`.
    - For each `system_prompt`, split it into `module_name` and `attribute_name` using the last period as the delimiter.
    - Attempt to retrieve the module using `getattr` on `prompts` with `module_name`.
    - If successful, append the `MESSAGE` attribute of the retrieved module's attribute to `formatted_prompts`.
    - If an `AttributeError` occurs, append a dictionary with `role` set to 'system' and `content` set to the original `system_prompt`.
    - Return the `formatted_prompts` list.
- **Output**:
    - A list of dictionaries, each representing a formatted system prompt, either resolved from a module's attribute or as a default dictionary with a 'system' role.


---
#### AgentConfiguration.tools
The `tools` function retrieves a list of tool classes based on the tool names specified in the agent configuration.
- **Inputs**:
    - None
- **Control Flow**:
    - Initialize an empty list `tools` to store tool classes.
    - Iterate over each `tool_name` in `self.tool_names`.
    - Check if `tool_name` exists in `TOOL_REGISTRY`.
    - If it exists, retrieve the corresponding tool class and append it to the `tools` list.
    - If it does not exist, raise an `AttributeError` indicating the tool could not be found.
    - Return the list of tool classes.
- **Output**:
    - A list of tool classes corresponding to the tool names in the agent configuration.



