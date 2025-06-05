# Purpose
This Python script is designed to function as an AWS Lambda handler that processes usage events and logs them into a database. The script is structured to handle logging configuration, establish a connection to AWS Secrets Manager for secure retrieval of database credentials, and manage database interactions using SQLModel. The logging setup ensures that log messages are appropriately captured and displayed based on the environment's log level settings. The script uses AWS Secrets Manager to securely fetch the database URL, which is then used to create a SQLAlchemy engine for database operations. The `get_engine` function ensures that the database engine is instantiated only once, optimizing resource usage.

The core functionality of the script is encapsulated in the `handler` function, which is the entry point for AWS Lambda. This function processes incoming event data, extracts relevant details, and creates a `UsageEvent` object that is then stored in the database. The `UsageEvent` model, imported from `database.models_v1`, represents the structure of the data being logged. The script is designed to handle synchronous operations, as required by AWS Lambda, and it ensures that each event is logged with its unique session ID and associated metadata. This setup is particularly useful for tracking and analyzing usage patterns in applications, providing a robust mechanism for event logging and data persistence in a cloud environment.
# Imports and Dependencies

---
- `logging`
- `os`
- `botocore`
- `aws_secretsmanager_caching.SecretCache`
- `aws_secretsmanager_caching.SecretCacheConfig`
- `database.models_v1.UsageEvent`
- `sqlmodel.Session`
- `sqlmodel.create_engine`
- `src.utils.config.settings`


# Global Variables

---
### cache 
- **Type**: `SecretCache`
- **Description**: The `cache` variable is an instance of the `SecretCache` class, which is part of the `aws_secretsmanager_caching` library. It is configured with a `SecretCacheConfig` and a `secretsmanager` client from the `botocore` library. This cache is used to efficiently retrieve and store secrets from AWS Secrets Manager, reducing the number of API calls and improving performance.
- **Use**: This variable is used to access secrets, such as the database URL, from AWS Secrets Manager in a cached manner.


---
### cache_config 
- **Type**: `SecretCacheConfig`
- **Description**: The `cache_config` variable is an instance of the `SecretCacheConfig` class from the `aws_secretsmanager_caching` library. This configuration object is used to define settings for the secret cache, which is responsible for managing and caching secrets retrieved from AWS Secrets Manager.
- **Use**: This variable is used to configure the `SecretCache` instance, which caches secrets for efficient retrieval.


---
### database_url 
- **Type**: `str`
- **Description**: The `database_url` variable is a string that holds the URL for connecting to the database. It is determined by retrieving a secret from AWS Secrets Manager if the environment is not 'local', otherwise it uses a predefined URL from the settings.
- **Use**: This variable is used to create a database engine for establishing connections to the database.


---
### engine 
- **Type**: `NoneType or sqlalchemy.engine.base.Engine`
- **Description**: The `engine` variable is a global variable that is initially set to `None` and is intended to hold a SQLAlchemy engine instance. It is used to manage database connections and is created using the `create_engine` function with a database URL when first accessed.
- **Use**: This variable is used to create and manage a connection pool to the database, facilitating database operations within the application.


---
### log_level 
- **Type**: `str`
- **Description**: The `log_level` variable is a string that represents the logging level for the application. It is set by retrieving the `LOG_LEVEL` environment variable, converting it to uppercase, or defaults to `logging.INFO` if the environment variable is not set.
- **Use**: This variable is used to configure the logging level for the application's logger, determining the severity of messages that will be logged.


---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `logging.Logger` class, which is used to log messages for the application. It is configured to use a log level that is determined by the `LOG_LEVEL` environment variable or defaults to `logging.INFO`. The logger is set up to either use an existing handler or configure a new one based on the environment.
- **Use**: This variable is used throughout the code to log informational messages, such as the log level setting and details of events processed by the handler function.


---
### sm_client 
- **Type**: `botocore.client.BaseClient`
- **Description**: The `sm_client` variable is an instance of a Boto3 client for AWS Secrets Manager, created using the `botocore.session.get_session().create_client` method. This client is used to interact with AWS Secrets Manager, allowing the application to retrieve and manage secrets securely.
- **Use**: This variable is used to create a `SecretCache` instance, which caches secrets retrieved from AWS Secrets Manager for efficient access.


# Functions

---
### get_engine 
The `get_engine` function returns a singleton SQLAlchemy engine instance, creating it if it doesn't already exist.
- **Inputs**:
    - None
- **Control Flow**:
    - The function checks if the global variable `engine` is `None`.
    - If `engine` is `None`, it initializes `engine` using `create_engine` with `database_url` and a pool size of 1.
    - The function returns the `engine` instance.
- **Output**:
    - The function returns an instance of a SQLAlchemy engine.


---
### handler 
The `handler` function processes an event by logging its details, storing it in a database, and returning the ID of the stored event.
- **Inputs**:
    - `event`: A dictionary containing event details, specifically under the 'detail' key, which includes information such as session_id, event_source, event_type, organization_id, user_id, bytes_in, bytes_out, tokens_in, tokens_out, timestamp, and event_metadata.
    - `context`: An object providing runtime information to the handler, typically used in AWS Lambda functions.
- **Control Flow**:
    - Log the event and context information using the logger.
    - Extract the 'detail' key from the event dictionary and log its content.
    - Open a database session using the SQLModel Session and the engine obtained from `get_engine()`.
    - Extract various fields from the event data such as session_id, event_source, etc.
    - Create a `UsageEvent` object with the extracted data.
    - Add the `UsageEvent` object to the session and commit the transaction to store it in the database.
    - Refresh the session to ensure the `UsageEvent` object is updated with any changes made during the commit, such as auto-generated IDs.
    - Return the ID of the stored `UsageEvent` as a string.
- **Output**:
    - A string representing the ID of the stored `UsageEvent`.


