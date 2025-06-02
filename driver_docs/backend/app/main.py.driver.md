# Purpose
This Python file is a configuration and initialization script for a FastAPI application, focusing on logging, error handling, and middleware setup. It defines a `FastAPI` application instance and configures it with various middleware components, including CORS, logging, and authentication. The script also sets up a custom logging format using a `JsonFormatter` class, which formats log messages as JSON objects, and initializes Sentry for error tracking across different environments (local, development, staging, and production). The Sentry configuration is environment-specific, adjusting settings like the trace sample rate and whether continuous profiling is enabled.

The script includes a custom function to generate unique route IDs and sets up a global exception handler to log unhandled exceptions and return a generic error response. The application is configured to include API routes from an external router module, and it uses settings imported from a configuration module to determine various parameters like log level, CORS origins, and Sentry DSN. This file serves as the entry point for the FastAPI application, orchestrating the setup of essential components and ensuring that the application is ready to handle requests with appropriate logging and error management.
# Imports and Dependencies

---
- `json`
- `logging`
- `logging.handlers`
- `datetime`
- `Formatter`
- `LogRecord`
- `Literal`
- `sentry_sdk`
- `fastapi.FastAPI`
- `fastapi.Request`
- `fastapi.responses.JSONResponse`
- `fastapi.routing.APIRoute`
- `starlette.middleware.cors.CORSMiddleware`
- `app.api.auth.AuthMiddleware`
- `app.api.logging_middleware.LoggingMiddleware`
- `app.api.main.api_router`
- `app.core.config.settings`


# Global Variables

---
### app 
- **Type**: `FastAPI`
- **Description**: The `app` variable is an instance of the FastAPI class, which is used to create a web application. It is configured with various settings such as the project name, OpenAPI URL, and a custom function for generating unique route IDs. Additionally, it includes middleware for CORS, logging, and authentication, and it registers the main API router.
- **Use**: This variable is used to define and configure the FastAPI application, including its routes, middleware, and exception handling.


---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `logging.Logger` class, obtained by calling `logging.getLogger(__name__)`. This creates a logger object that is associated with the module's name, allowing for module-specific logging.
- **Use**: This logger is used throughout the module to log messages, warnings, and errors, facilitating debugging and monitoring of the application's behavior.


# Classes

---
### JsonFormatter 
- **Type**: `class`
- **Members**:
    - `format`: Formats a LogRecord into a JSON string with specific fields.
- **Description**: The JsonFormatter class is a custom logging formatter that extends the base Formatter class to output log records in JSON format. It overrides the format method to convert log record attributes such as level, timestamp, name, and message into a JSON object. Additionally, if an exception is present in the log record, it includes a traceback in the JSON output. This formatter is useful for structured logging, making it easier to parse and analyze log data.
- **Inherits From**:
    - Formatter

**Methods**

---
#### JsonFormatter.__init__
The `__init__` function initializes an instance of the `JsonFormatter` class by calling the constructor of its superclass, `Formatter`.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls the `__init__` method of the superclass `Formatter` using `super().__init__()`.
- **Output**:
    - The function does not return any value; it initializes the object.


---
#### JsonFormatter.format
The `format` function formats a log record into a JSON string with specific fields.
- **Inputs**:
    - `record`: A `LogRecord` object containing information about the log event, such as level, timestamp, name, message, and exception info.
- **Control Flow**:
    - Initialize an empty dictionary `json_record` to store log information.
    - Extract the log level name from the `record` and store it in `json_record` under the key 'level'.
    - Convert the timestamp from the `record` to a formatted string and store it in `json_record` under the key 'timestamp'.
    - Extract the logger name from the `record` and store it in `json_record` under the key 'name'.
    - Retrieve the log message from the `record` using `getMessage()` and store it in `json_record` under the key 'message'.
    - Check if there is exception information in the `record` using `record.exc_info`.
    - If exception information is present, format it using `self.formatException(record.exc_info)` and store it in `json_record` under the key 'traceback'.
    - Convert the `json_record` dictionary to a JSON string using `json.dumps()` and return it.
- **Output**:
    - A JSON string representing the log record with fields for level, timestamp, name, message, and optionally traceback if exception info is present.



# Functions

---
### configure_logging 
The `configure_logging` function sets up the logging configuration for the application using a JSON formatter and a specified log level.
- **Inputs**:
    - None
- **Control Flow**:
    - Retrieve the log level from the settings and convert it to uppercase.
    - Create a new logging stream handler.
    - Set the formatter of the handler to an instance of `JsonFormatter`.
    - Configure the basic logging settings with the specified log level and handler.
    - Log an informational message indicating the log level that has been set.
- **Output**:
    - The function does not return any value; it configures the logging settings for the application.


---
### configure_sentry 
The `configure_sentry` function initializes Sentry SDK based on the specified environment to handle error tracking and performance monitoring.
- **Inputs**:
    - `environment`: A string literal indicating the environment type, which can be 'local', 'development', 'staging', or 'production'.
    - `dsn`: A string representing the Data Source Name (DSN) for Sentry, used to authenticate and send data to the Sentry server.
- **Control Flow**:
    - The function uses a match-case statement to determine the configuration based on the `environment` argument.
    - If the environment is 'local', the function does nothing and exits.
    - For 'development', 'staging', and 'production', the function initializes the Sentry SDK with different configurations for each environment, including setting the `environment`, `send_default_pii`, `traces_sample_rate`, and `_experiments` parameters.
    - If the environment does not match any of the specified cases, a warning is logged indicating that the environment is unrecognized and Sentry is not configured.
- **Output**:
    - The function does not return any value; it performs side effects by configuring the Sentry SDK.


---
### custom_generate_unique_id 
The `custom_generate_unique_id` function generates a unique identifier for an API route by combining its first tag and name.
- **Inputs**:
    - `route`: An instance of `APIRoute` which contains metadata about the API route, including tags and name.
- **Control Flow**:
    - The function accesses the first tag of the `route` object using `route.tags[0]`.
    - It accesses the name of the `route` object using `route.name`.
    - It concatenates the first tag and the name with a hyphen in between to form a unique identifier.
- **Output**:
    - A string that represents a unique identifier for the given API route, formatted as '<first_tag>-<route_name>'.


---
### global_exception_handler 
The `global_exception_handler` function logs unhandled exceptions and returns a JSON response with a 500 status code.
- **Inputs**:
    - `request`: An instance of `Request` representing the HTTP request that caused the exception.
    - `exc`: An instance of `Exception` representing the unhandled exception that occurred.
- **Control Flow**:
    - Logs the unhandled exception using the `logging.error` method, including exception information.
    - Returns a `JSONResponse` with a status code of 500 and a message indicating that an error occurred and has been logged.
- **Output**:
    - A `JSONResponse` object with a 500 status code and a message indicating an error has occurred and been logged.


