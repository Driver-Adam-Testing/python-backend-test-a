
## Files
- **[agent_code_critic.py](agents/agent_code_critic.py.driver.md)**: The `agent_code_critic.py` file implements functionality for extracting, verifying, and correcting code snippets using an OpenAI-based agent within a pipeline configuration.
- **[agent_copy_editor.py](agents/agent_copy_editor.py.driver.md)**: The `agent_copy_editor.py` file defines a function to run a copy editing agent using a specified configuration and session, with support for handling specific prompt types and generating a response.
- **[agent_default.py](agents/agent_default.py.driver.md)**: The `agent_default.py` file defines a function to run a default agent using specified configurations and sessions, and returns a structured response.
- **[agent_edit_document.py](agents/agent_edit_document.py.driver.md)**: The `agent_edit_document.py` file defines a pipeline for editing a document by generating smart instructions to rewrite selected text, utilizing various agents for prompt augmentation, default processing, and copy editing.
- **[agent_prompt_augmentation.py](agents/agent_prompt_augmentation.py.driver.md)**: The `agent_prompt_augmentation.py` file defines a function to augment prompts using an agent, with constraints on prompt length and a response model to capture the augmented prompt and its rationale.
- **[execute.py](agents/execute.py.driver.md)**: The `execute.py` file in the `python-backend` codebase defines functions to validate and execute a sequence of pipeline steps, utilizing various agents for tasks such as prompt augmentation, code critique, and copy editing.
