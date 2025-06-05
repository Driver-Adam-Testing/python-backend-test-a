# Purpose
This code defines a custom extension for a GraphQL server using the Strawberry library, specifically for logging purposes. It provides narrow functionality by extending the `SchemaExtension` class to log the beginning of a GraphQL query execution. The `LoggingExtension` class overrides the `on_execute` method, which logs the first 128 characters of the query, removing any newline characters, to the configured logger. This is a short script that enhances observability by integrating logging into the GraphQL execution process, allowing developers to monitor and debug queries being executed on the server.
# Imports and Dependencies

---
- `logging`
- `collections.abc.Iterator`
- `strawberry.extensions.base_extension.SchemaExtension`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from Python's `logging` module. It is configured to use the module's name as its logger name, which is typically the `__name__` attribute of the module where it is defined. This allows for hierarchical logging and easy identification of log messages from different parts of the application.
- **Use**: This variable is used to log informational messages, particularly within the `LoggingExtension` class, to track GraphQL query executions.


# Classes

---
### LoggingExtension 
- **Type**: `class`
- **Members**:
    - `on_execute`: Logs the first 128 characters of the GraphQL query being executed.
- **Description**: The LoggingExtension class is a subclass of SchemaExtension that provides logging functionality for GraphQL queries. It overrides the on_execute method to log the first 128 characters of the query being executed, removing any newline characters for cleaner logging output. This class is useful for monitoring and debugging GraphQL queries by providing a simple way to log query information during execution.
- **Inherits From**:
    - SchemaExtension

**Methods**

---
#### LoggingExtension.on_execute
The `on_execute` function logs the first 128 characters of a GraphQL query from the execution context and yields control.
- **Inputs**:
    - None
- **Control Flow**:
    - Logs the first 128 characters of the GraphQL query from the execution context, replacing any newline characters with an empty string.
    - Yields control back to the caller, allowing for further processing or continuation of execution.
- **Output**:
    - An iterator that yields `None`, indicating the function is a generator.



