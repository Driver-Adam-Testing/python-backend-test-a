## Folders
- **[audience](prompts/audience.driver.md)**: The `audience` folder in the `python-backend` codebase contains various Python files that provide tailored prompts and content for different audiences, including business development professionals, fifth graders, product managers, and software engineers.
- **[block_kind](prompts/block_kind.driver.md)**: The `block_kind` folder in the `python-backend` codebase contains Python files that define Pydantic models and classes for converting various content types, such as code blocks, diagrams, lists, tables, and text, into markdown format for a copy editor agent.
- **[interface](prompts/interface.driver.md)**: The `interface` folder in the `python-backend` codebase contains various Python files that define and initialize system prompts and interfaces for executing tools iteratively, managing technical context, and ensuring thoughtful communication.
- **[task](prompts/task.driver.md)**: The `task` folder in the `python-backend` codebase contains various Python scripts that provide prompts and system messages for tasks related to technical document creation, code verification, extraction, editing, and syntax handling.
- **[tools](prompts/tools.driver.md)**: The `tools` folder in the `python-backend` codebase contains initialization and module import files, specifically an `__init__.py` for package marking and a `think.py` for importing a `think` module and defining a `PROMPT` variable.
- **[voice](prompts/voice.driver.md)**: The `voice` folder in the `python-backend` codebase contains initialization and module files that define prompts and roles for technical copy editing, content pipeline operations, and software engineering expertise.

## Files
- **[__init__.py](prompts/__init__.py.driver.md)**: The `__init__.py` file in the `python-backend` codebase initializes the `shared.prompts` package by importing the `audience`, `interface`, `task`, and `voice` modules.
