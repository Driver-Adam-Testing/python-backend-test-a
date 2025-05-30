
## Files
- **[__init__.py](core/__init__.py.driver.md)**: Empty file (no analyzable contents).
- **[config.py](core/config.py.driver.md)**: The `config.py` file defines a `Settings` class using Pydantic to manage application configuration, including environment variables, API settings, and secret management, with a mechanism to warn or raise errors if default secrets are not changed.
- **[logger.py](core/logger.py.driver.md)**: The `logger.py` file sets up a logging configuration with a stream handler for outputting warning and above level logs to the console, but includes a note indicating it should be deprecated in favor of a logger in `main.py`.
