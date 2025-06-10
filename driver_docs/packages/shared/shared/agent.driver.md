## Folders
- **[models](agent/models.driver.md)**: The `models` folder in the `python-backend` codebase contains configurations and utility functions for handling language models from providers like OpenAI, Anthropic, and Google, with subfolders for specific models such as `claude` and `openai`, and files for model configuration and initialization.
- **[tools](agent/tools.driver.md)**: The `tools` folder in the `python-backend` codebase contains various Python files that define and register tools for operations such as searching, opening files, and summarizing codebase folders, with a focus on handling content retrieval and execution logic.

## Files
- **[__init__.py](agent/__init__.py.driver.md)**: Empty file (no analyzable contents).
- **[agent_anthropic_strict.py](agent/agent_anthropic_strict.py.driver.md)**: The `agent_anthropic_strict.py` file defines the `AnthropicStrictAgent` class, which extends `AgentBase` to handle tool calls and message completions using the Anthropic client, with optional response formatting.
- **[agent_base.py](agent/agent_base.py.driver.md)**: The `agent_base.py` file defines an abstract base class `AgentBase` for managing agent instances, including logging, message handling, and iteration control, with abstract methods for generating responses and executing iterations.
- **[agent_factory.py](agent/agent_factory.py.driver.md)**: The `agent_factory.py` file defines a function to create and return either an `OpenAIStrictAgent` or an `AnthropicStrictAgent` based on the specified model configuration and provider.
- **[agent_openai_strict.py](agent/agent_openai_strict.py.driver.md)**: The `agent_openai_strict.py` file defines the `OpenAIStrictAgent` class, which extends `AgentBase` to interact with OpenAI's API, manage tool calls, and generate responses with strict adherence to tool usage and message handling.
- **[chat_openai.py](agent/chat_openai.py.driver.md)**: The `chat_openai.py` file defines a `ChatOpenAI` class for generating responses using OpenAI's API, with support for different output configurations and retry logic for handling API errors.
