# Purpose
This Python source code file defines a set of utility decorators that enhance the functionality of functions by adding caching, logging suppression, and retry mechanisms with exponential backoff. The `expiring_cache` decorator provides a thread-safe caching mechanism that stores the result of a function call for a specified duration, after which the cache is invalidated and the function is called again. This is achieved using a lock to ensure thread safety. The `suppress_logging` decorator temporarily suppresses logging messages for the duration of a function call, restoring the original logging level afterward. This can be useful for reducing log noise during specific operations.

Additionally, the file includes two retry decorators: `async_retry_with_exponential_backoff` and `retry_with_exponential_backoff`. These decorators implement retry logic with exponential backoff for asynchronous and synchronous functions, respectively. They attempt to re-execute a function upon encountering specified exceptions, increasing the delay between retries exponentially, with optional jitter to randomize the delay slightly. These decorators are useful for handling transient errors in network or I/O operations, ensuring robustness in applications that require reliable execution despite occasional failures. Overall, the file serves as a library of decorators that can be imported and used to enhance the reliability and efficiency of function calls in Python applications.
# Imports and Dependencies

---
- `logging`
- `random`
- `time`
- `traceback`
- `typing`
- `collections.abc`
- `functools`
- `threading`


# Global Variables

---
### RET_TYPE 
- **Type**: `typing.TypeVar`
- **Description**: `RET_TYPE` is a type variable defined using `typing.TypeVar`, which allows for generic programming by enabling the specification of a placeholder for a type that can be used in function signatures. It is used to indicate that a function can return any type, and this type will be consistent across the function's usage.
- **Use**: `RET_TYPE` is used in function decorators to specify that the decorated function can return any type, maintaining type consistency.


---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module, configured to use the current module's name as its logger name. It is used to log messages with different severity levels, such as info and debug, throughout the module.
- **Use**: This variable is used to log informational messages and debug information, particularly in the context of cache expiration and retry operations.


# Functions

---
### async_retry_with_exponential_backoff 
The function `async_retry_with_exponential_backoff` is a decorator that retries an asynchronous function with exponential backoff upon encountering specified exceptions.
- **Inputs**:
    - `initial_delay`: A float representing the initial delay in seconds before the first retry.
    - `exponential_base`: A float that serves as the base for the exponential backoff calculation.
    - `jitter`: A boolean indicating whether to add randomness to the delay to prevent thundering herd problems.
    - `max_retries`: An integer specifying the maximum number of retry attempts before giving up.
    - `errors`: A tuple of exception classes that should trigger a retry when raised by the decorated function.
- **Control Flow**:
    - Define a decorator function `retry_decorator` that takes a function `func` as an argument.
    - Within `retry_decorator`, define an asynchronous wrapper function `wrapper` that accepts arbitrary positional and keyword arguments.
    - Initialize `num_retries` to 0 and `delay` to `initial_delay`.
    - Enter an infinite loop to attempt calling the asynchronous function `func`.
    - Use a try-except block to catch exceptions specified in `errors`.
    - If the function call is successful, return its result immediately.
    - If an exception is caught, log the exception and increment `num_retries`.
    - Check if `num_retries` exceeds `max_retries`; if so, raise an exception indicating the retry limit has been exceeded.
    - Calculate the next delay using exponential backoff and optional jitter, then log the retry attempt.
    - Pause execution for the calculated delay using `time.sleep(delay)`.
    - If an exception not specified in `errors` is raised, re-raise it immediately.
- **Output**:
    - The function returns a decorator that can be applied to an asynchronous function, enabling it to be retried with exponential backoff upon encountering specified exceptions.


---
### clear_cache 
The `clear_cache` function resets the cache by setting its value to None and expiration time to zero, ensuring thread safety with a lock.
- **Inputs**:
    - None
- **Control Flow**:
    - The function acquires a lock to ensure thread safety when modifying the cache.
    - It updates the cache dictionary by setting 'value' to None and 'expires_at' to 0, effectively clearing the cache.
- **Output**:
    - The function does not return any value (returns None).


---
### decorator 
The `decorator` function is a higher-order function that provides caching with expiration for another function's result, ensuring thread safety using a lock.
- **Inputs**:
    - `func`: A callable function whose result is to be cached.
- **Control Flow**:
    - Initialize a cache dictionary with keys 'value' and 'expires_at'.
    - Create a lock object to ensure thread safety.
    - Define an inner function `wrapped` that takes any arguments and keyword arguments.
    - Within `wrapped`, get the current time and acquire the lock.
    - Check if the cache has expired by comparing the current time with 'expires_at'.
    - If expired, log a message, call the original function, and update the cache with the new value and expiration time.
    - Return the cached value.
    - Define a `clear_cache` function to reset the cache, ensuring thread safety with the lock.
    - Attach `clear_cache` to the `wrapped` function as an attribute.
    - Return the `wrapped` function.
- **Output**:
    - A wrapped version of the input function with caching and cache clearing capabilities.


---
### expiring_cache 
The `expiring_cache` function is a decorator that caches the result of a function for a specified duration, ensuring thread safety with a lock.
- **Inputs**:
    - `duration_sec`: The duration in seconds for which the cache is valid before it expires and the function is called again.
- **Control Flow**:
    - The `expiring_cache` function takes `duration_sec` as an argument and returns a decorator function `decorator`.
    - Inside `decorator`, a cache dictionary is initialized with keys `value` and `expires_at`, and a `Lock` object is created for thread safety.
    - The `decorator` function defines a `wrapped` function that checks if the cache has expired by comparing the current time with `expires_at`.
    - If the cache has expired, the original function is called, its result is stored in the cache, and `expires_at` is updated to the current time plus `duration_sec`.
    - The `wrapped` function returns the cached value.
    - A `clear_cache` function is defined within `decorator` to reset the cache, and it is attached to `wrapped` as an attribute.
    - The `decorator` function returns the `wrapped` function.
- **Output**:
    - The function returns a decorator that, when applied to another function, caches its result for a specified duration and provides a method to clear the cache.


---
### retry_decorator 
The `retry_decorator` function is an asynchronous decorator that retries a given function with exponential backoff upon encountering specified exceptions.
- **Inputs**:
    - `func`: The function to be decorated and retried upon failure.
- **Control Flow**:
    - Initialize `num_retries` to 0 and `delay` to `initial_delay`.
    - Enter an infinite loop to attempt executing the function `func`.
    - Use a try-except block to catch specified exceptions (`errors`).
    - If the function call is successful, return its result immediately.
    - If an exception in `errors` is caught, log the exception and increment `num_retries`.
    - Check if `num_retries` exceeds `max_retries`; if so, raise an exception indicating the maximum retries have been exceeded.
    - Calculate the next delay using exponential backoff with optional jitter and log the retry attempt.
    - Pause execution for the calculated delay using `time.sleep(delay)`.
    - If an exception not in `errors` is caught, re-raise it immediately.
- **Output**:
    - The output is the result of the successfully executed function `func`, or an exception if the maximum number of retries is exceeded or an unexpected exception occurs.


---
### retry_with_exponential_backoff 
The function `retry_with_exponential_backoff` is a decorator that retries a function call with exponential backoff in case of specified exceptions.
- **Inputs**:
    - `initial_delay`: The initial delay in seconds before the first retry attempt.
    - `exponential_base`: The base of the exponential function used to calculate the delay for retries.
    - `jitter`: A boolean indicating whether to add randomness to the delay to prevent thundering herd problem.
    - `max_retries`: The maximum number of retry attempts before giving up.
    - `errors`: A tuple of exception types that should trigger a retry.
- **Control Flow**:
    - Define a decorator function `retry_decorator` that takes a function `func` as an argument.
    - Inside `retry_decorator`, define a `wrapper` function that will execute the retry logic.
    - Initialize `num_retries` to 0 and `delay` to `initial_delay`.
    - Enter a `while True` loop to repeatedly attempt to call `func`.
    - Try to execute `func` with the provided arguments and return its result if successful.
    - Catch exceptions specified in `errors`, log the exception, and increment `num_retries`.
    - If `num_retries` exceeds `max_retries`, raise an exception indicating the maximum retries have been exceeded.
    - Calculate the next delay using exponential backoff and optional jitter, then log the retry attempt.
    - Pause execution for the calculated delay using `time.sleep(delay)`.
    - If an exception not specified in `errors` is raised, re-raise it immediately.
- **Output**:
    - Returns a decorator function that can be used to wrap another function, adding retry logic with exponential backoff.


---
### suppress_logging 
The `suppress_logging` function is a decorator that temporarily suppresses logging messages by setting the logging level to CRITICAL during the execution of the decorated function.
- **Inputs**:
    - `func`: A callable function that the decorator will wrap and execute with suppressed logging.
- **Control Flow**:
    - The function `suppress_logging` is defined as a decorator that takes a single argument `func`, which is a callable.
    - Inside `suppress_logging`, a nested function `wrapper` is defined, which wraps the original function `func`.
    - The `wrapper` function retrieves the current logger using `logging.getLogger()` and stores the current logging level using `getEffectiveLevel()`.
    - The logging level is then set to `logging.CRITICAL` to suppress all logging messages below this level.
    - The original function `func` is called with any provided arguments and keyword arguments, and its result is returned.
    - Finally, the logging level is restored to its original state using a `finally` block to ensure it happens even if an exception is raised during the function call.
    - The `wrapper` function is returned from `suppress_logging`, effectively replacing the original function with the wrapped version.
- **Output**:
    - The output is a callable that behaves like the original function but with logging messages suppressed during its execution.


---
### wrapped 
The `wrapped` function caches the result of a decorated function and refreshes the cache after a specified duration if it has expired.
- **Inputs**:
    - `*args`: Positional arguments to be passed to the decorated function.
    - `**kwargs`: Keyword arguments to be passed to the decorated function.
- **Control Flow**:
    - Retrieve the current time using `time.time()`.
    - Acquire a lock to ensure thread safety when accessing the cache.
    - Check if the cache's expiration time has passed the current time.
    - If the cache has expired, log a message indicating the cache expiration and call the decorated function with the provided arguments to refresh the cache value.
    - Update the cache's expiration time by adding the specified duration to the current time.
    - Return the cached value.
- **Output**:
    - The function returns the cached result of the decorated function, refreshing it if the cache has expired.


---
### wrapper 
The `wrapper` function is a decorator that temporarily suppresses logging messages by setting the logging level to CRITICAL while executing the decorated function.
- **Inputs**:
    - `*args`: A tuple of positional arguments to be passed to the decorated function.
    - `**kwargs`: A dictionary of keyword arguments to be passed to the decorated function.
- **Control Flow**:
    - Retrieve the root logger using `logging.getLogger()`.
    - Store the current logging level using `logger.getEffectiveLevel()`.
    - Set the logging level to CRITICAL to suppress logging messages.
    - Attempt to execute the decorated function `func` with the provided `*args` and `**kwargs`.
    - After the function execution, restore the original logging level regardless of whether the function execution was successful or raised an exception.
- **Output**:
    - The output is the return value of the decorated function `func`, executed with the provided arguments.


