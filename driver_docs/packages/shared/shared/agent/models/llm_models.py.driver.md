# Purpose
This Python code defines a configuration management system for machine learning models, specifically focusing on language models. It is structured as a library file intended to be imported and used in other parts of a software application. The code leverages the `pydantic` library to define a `ModelConfig` class, which serves as a data model for storing and validating configuration details of language models. The configuration includes attributes such as `model_name`, `model_id`, `provider`, `context_window_size`, `max_output_tokens`, and `system_prompts`. The `ModelProvider` and `SystemPromptConfig` enums define possible values for the model provider and system prompt configurations, respectively.

The code provides functionality to load model configurations from a TOML file named `llm_model_config.toml`, which is expected to be located in the same directory as the script. The `ModelConfig` class includes class methods `default` and `from_name` to retrieve model configurations by name, with `from_name` reading the configuration details from the TOML file. This setup allows for flexible and dynamic loading of model configurations, making it easy to manage and switch between different model setups. The code raises a `ValueError` if a requested model configuration is not found, ensuring robust error handling.
# Imports and Dependencies

---
- `os`
- `enum`
- `toml`
- `pydantic`


# Global Variables

---
### ANTHROPIC 
- **Type**: `Enum`
- **Description**: `ANTHROPIC` is a member of the `ModelProvider` enumeration, which defines a set of possible model providers. In this context, `ANTHROPIC` represents a specific model provider option that can be used within the application.
- **Use**: This variable is used to specify 'anthropic' as a model provider option in the `ModelProvider` enum.


---
### GOOGLE 
- **Type**: `Enum`
- **Description**: The `GOOGLE` variable is a member of the `ModelProvider` enumeration, which defines a set of constants representing different model providers. In this case, `GOOGLE` is one of the possible values, indicating that the model provider is Google.
- **Use**: This variable is used to specify Google as a model provider when configuring or selecting a model in the application.


---
### MANY 
- **Type**: `SystemPromptConfig`
- **Description**: `MANY` is a member of the `SystemPromptConfig` enumeration, which is a subclass of `str` and `Enum`. It represents one of the possible configurations for system prompts, specifically indicating a configuration where multiple prompts are used.
- **Use**: This variable is used to specify a configuration option for system prompts within the application, allowing the system to handle multiple prompts.


---
### NONE 
- **Type**: `Enum`
- **Description**: `NONE` is a member of the `SystemPromptConfig` enumeration, which is a subclass of `str` and `Enum`. It represents a configuration option for system prompts, specifically indicating the absence of any system prompts.
- **Use**: This variable is used to specify that no system prompts should be applied in the configuration settings.


---
### ONE 
- **Type**: `str`
- **Description**: `ONE` is a member of the `SystemPromptConfig` enumeration, which is a subclass of `str` and `Enum`. It represents a specific configuration option for system prompts, indicating a single prompt configuration.
- **Use**: This variable is used to specify a configuration option for system prompts within the `SystemPromptConfig` enumeration.


---
### OPENAI 
- **Type**: `Enum`
- **Description**: `OPENAI` is a member of the `ModelProvider` enumeration, which represents different model providers available in the system. It is assigned the string value "openai".
- **Use**: This variable is used to specify the OpenAI model provider when configuring or selecting a model in the application.


# Classes

---
### ModelConfig 
- **Type**: `class`
- **Members**:
    - `model_name`: The name of the model.
    - `model_id`: The unique identifier for the model.
    - `provider`: The provider of the model, such as OpenAI or Google.
    - `context_window_size`: The size of the context window for the model.
    - `max_output_tokens`: The maximum number of tokens the model can output.
    - `system_prompts`: The system prompts configuration for the model.
- **Description**: The `ModelConfig` class is a configuration model that inherits from `BaseModel` and is used to define and manage the configuration settings for a language model. It includes attributes such as `model_name`, `model_id`, `provider`, `context_window_size`, `max_output_tokens`, and `system_prompts`, which are essential for identifying and configuring the model's behavior. The class provides class methods `default` and `from_name` to load model configurations from a TOML file, allowing for easy retrieval and instantiation of model configurations based on a given model name.
- **Inherits From**:
    - BaseModel

**Methods**

---
#### ModelConfig.default
The `default` function returns a `ModelConfig` instance using the default model configuration.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is a class method of `ModelConfig`.
    - It calls another class method `from_name` with the argument 'default'.
    - The `from_name` method attempts to load a model configuration from a TOML file using the provided model name.
    - If a matching model configuration is found, it returns a `ModelConfig` instance with the loaded details.
    - If no matching configuration is found, a `ValueError` is raised.
- **Output**:
    - A `ModelConfig` instance initialized with the default model configuration.


---
#### ModelConfig.from_name
The `from_name` function retrieves a model configuration from a TOML file based on a given model name or ID and returns a `ModelConfig` instance.
- **Inputs**:
    - `cls`: The class reference, typically `ModelConfig`, used to create an instance of the class.
    - `model_name`: A string representing the name or ID of the model to retrieve the configuration for, defaulting to 'default'.
- **Control Flow**:
    - Constructs the path to the 'llm_model_config.toml' file located in the same directory as the script.
    - Loads the model configuration data from the TOML file using the `toml.load` function.
    - Iterates over the models in the configuration file, checking if the `model_id` or the model name matches the provided `model_name`.
    - If a match is found, returns an instance of `ModelConfig` initialized with the details from the configuration file.
    - If no matching model is found, raises a `ValueError` indicating the model configuration was not found.
- **Output**:
    - Returns an instance of `ModelConfig` initialized with the details of the specified model from the configuration file.



---
### ModelProvider 
- **Type**: `class`
- **Members**:
    - `OPENAI`: Represents the OpenAI model provider.
    - `ANTHROPIC`: Represents the Anthropic model provider.
    - `GOOGLE`: Represents the Google model provider.
- **Description**: The `ModelProvider` class is an enumeration that defines a set of constants representing different model providers, specifically 'openai', 'anthropic', and 'google'. It inherits from both `str` and `Enum`, allowing each member to be treated as a string while also being part of an enumeration. This class is useful for standardizing the representation of model providers across the application.
- **Inherits From**:
    - str
    - Enum


---
### SystemPromptConfig 
- **Type**: `enum`
- **Members**:
    - `NONE`: Represents a configuration with no system prompts.
    - `ONE`: Represents a configuration with one system prompt.
    - `MANY`: Represents a configuration with many system prompts.
- **Description**: The `SystemPromptConfig` class is an enumeration that defines different configurations for system prompts, allowing for the specification of whether there are no prompts, one prompt, or many prompts. It inherits from both `str` and `Enum`, enabling it to be used as a string while also providing enumeration capabilities.
- **Inherits From**:
    - str
    - Enum


