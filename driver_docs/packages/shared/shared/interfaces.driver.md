## Folders
- **[agents](interfaces/agents.driver.md)**: The `agents` folder in the `python-backend` codebase contains Python files that define classes and configurations for managing agent operations, including agent configuration, block types and responses, data scope management, pipeline configuration, and prompt handling.
- **[billing](interfaces/billing.driver.md)**: The `billing` folder in the `python-backend` codebase contains files related to defining data models for subscription records and requests, with an empty `__init__.py` file and a `subscription_schema.py` file that specifies subscription-related data models.
- **[file_content](interfaces/file_content.driver.md)**: The `file_content` folder in the `python-backend` codebase contains Python files that define models and classes for handling and representing processed file content, including specific handling for PDF files.
- **[usage](interfaces/usage.driver.md)**: The `usage` folder in the `python-backend` codebase contains files that define and test data models and utilities for handling and converting usage metrics and events.

## Files
- **[__init__.py](interfaces/__init__.py.driver.md)**: Empty file (no analyzable contents).
- **[aws_client_config.py](interfaces/aws_client_config.py.driver.md)**: The `aws_client_config.py` file defines a Pydantic model for AWS client configuration, including region name, access key ID, and secret access key.
- **[request.py](interfaces/request.py.driver.md)**: The `request.py` file defines data models for driver requests using Pydantic, including `DriverRequest`, `DriverModalRequest`, and `DriverModalBatchRequest` classes.
- **[response.py](interfaces/response.py.driver.md)**: The `response.py` file defines a Pydantic model `DriverResponse` and a subclass `DriverModalResponse` with an additional `call_id` attribute.
- **[search.py](interfaces/search.py.driver.md)**: The `search.py` file defines classes and enums for handling search operations, including input parameters and results, using different search algorithms within the `python-backend` codebase.
