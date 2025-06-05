# Purpose
This Python script is designed to initialize a service by ensuring that a database connection is successfully established. It uses the SQLAlchemy and SQLModel libraries to interact with the database and the Tenacity library to implement a retry mechanism. The script defines a `main` function that logs the start of the initialization process, calls the `init` function to attempt a database connection, and logs the completion of the initialization. The `init` function uses a retry decorator to repeatedly attempt to create a session with the database engine, logging attempts and errors, until a successful connection is made or the maximum number of attempts is reached.

The script is structured to be executed as a standalone program, as indicated by the `if __name__ == "__main__":` block, which calls the `main` function. The use of logging provides visibility into the initialization process, and the retry mechanism ensures robustness by handling transient database connectivity issues. This code is not intended to be a library or module for import but rather a script to be run to initialize a service that depends on a database being ready and accessible.
# Imports and Dependencies

---
- `logging`
- `database.db.engine`
- `sqlalchemy.Engine`
- `sqlmodel.Session`
- `sqlmodel.select`
- `tenacity.after_log`
- `tenacity.before_log`
- `tenacity.retry`
- `tenacity.stop_after_attempt`
- `tenacity.wait_fixed`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module. It is configured to log messages with a level of INFO or higher. The logger is used to record informational and error messages throughout the application, particularly during the initialization of the database connection.
- **Use**: This variable is used to log messages before and after retry attempts, as well as to log errors and informational messages during the execution of the program.


---
### max_tries 
- **Type**: `int`
- **Description**: The variable `max_tries` is an integer that represents the maximum number of retry attempts allowed for a certain operation. It is calculated as 60 multiplied by 5, which equals 300, indicating a total of 5 minutes worth of attempts if each attempt is spaced by 1 second.
- **Use**: This variable is used to define the stopping condition for the retry mechanism in the `init` function, limiting the number of retry attempts to 300.


---
### wait_seconds 
- **Type**: `int`
- **Description**: The `wait_seconds` variable is an integer that specifies the fixed amount of time, in seconds, to wait between retry attempts when initializing the database connection. It is used in conjunction with the `tenacity` library to handle retries with a fixed wait time.
- **Use**: This variable is used to define the wait time between retry attempts in the `retry` decorator applied to the `init` function.


# Functions

---
### init 
The `init` function attempts to establish a session with a database engine to verify its availability, retrying on failure.
- **Inputs**:
    - `db_engine`: An instance of `Engine` from SQLAlchemy, representing the database connection to be tested.
- **Control Flow**:
    - The function is decorated with `@retry`, which configures it to retry on failure up to a specified number of attempts (`max_tries`) with a fixed wait time (`wait_seconds`) between attempts.
    - Within the function, a `try` block is used to attempt to create a session with the provided `db_engine`.
    - A `Session` object is created using the `db_engine`, and a simple SQL `select(1)` query is executed to check if the database is responsive.
    - If the session creation or query execution fails, an `Exception` is caught, logged as an error, and then re-raised to trigger a retry.
- **Output**:
    - The function does not return any value; it raises an exception if the database is not available after the retry attempts.


---
### main 
The `main` function initializes a service by logging the start and end of the initialization process and calling the `init` function to ensure the database engine is ready.
- **Inputs**:
    - None
- **Control Flow**:
    - Logs the message 'Initializing service' to indicate the start of the service initialization.
    - Calls the `init` function with the `engine` to check if the database is ready.
    - Logs the message 'Service finished initializing' to indicate the completion of the service initialization.
- **Output**:
    - The function does not return any value; it performs logging and calls the `init` function to initialize the service.


