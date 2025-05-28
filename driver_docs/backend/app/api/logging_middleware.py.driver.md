# Purpose
This code defines a custom middleware class, `LoggingMiddleware`, for a FastAPI application, which is a web framework for building APIs with Python. The middleware provides narrow functionality focused on logging HTTP request details, such as the request method, URL path, client IP address, status code, and response time. It generates a unique request ID using the `uuid` module and calculates the response time by measuring the duration between the request's start and end times. The logging is performed using Python's built-in `logging` module, and the middleware is designed to be integrated into the request-response cycle of a FastAPI application by extending `BaseHTTPMiddleware` from the Starlette framework. This code is a concise implementation of a logging mechanism to aid in monitoring and debugging API requests.
# Imports and Dependencies

---
- `logging`
- `uuid`
- `collections.abc.Callable`
- `datetime.datetime`
- `fastapi.Request`
- `fastapi.Response`
- `starlette.middleware.base.BaseHTTPMiddleware`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the Python `logging` module. It is configured to use the default logger, which is typically the root logger, as indicated by the use of `__name__` as the logger name.
- **Use**: This logger is used to log informational messages about HTTP requests processed by the `LoggingMiddleware`, including request ID, method, URL path, client IP, status code, and response time.


# Classes

---
### LoggingMiddleware 
- **Type**: `class`
- **Members**:
    - `dispatch`: Asynchronously processes an HTTP request, logs request and response details, and returns the response.
- **Description**: The `LoggingMiddleware` class is a custom middleware for FastAPI applications that extends `BaseHTTPMiddleware`. It intercepts HTTP requests, logs detailed information including a unique request ID, request method, URL path, client IP address, response status code, and response time in milliseconds. This middleware is useful for tracking and debugging HTTP requests and responses in a FastAPI application.
- **Inherits From**:
    - BaseHTTPMiddleware

**Methods**

---
#### LoggingMiddleware.dispatch
The `dispatch` function is an asynchronous middleware method that logs HTTP request details and response time for each request processed by a FastAPI application.
- **Inputs**:
    - `request`: An instance of `Request` representing the incoming HTTP request.
    - `call_next`: A callable that takes a `Request` and returns a `Response`, representing the next middleware or endpoint in the request processing chain.
- **Control Flow**:
    - Generate a unique request ID using `uuid.uuid4()` for tracking the request.
    - Record the current time to calculate the response time later.
    - Invoke the `call_next` callable with the `request` to get the `response`, allowing the request to proceed through the middleware chain.
    - Calculate the response time by subtracting the recorded start time from the current time after receiving the response.
    - Log the request ID, HTTP method, URL path, client IP address (from 'X-Forwarded-For' header if available, otherwise from `request.client.host`), response status code, and response time in milliseconds using the `logger`.
    - Return the `response` to continue the request processing.
- **Output**:
    - The function returns a `Response` object, which is the result of the `call_next` callable, representing the HTTP response to be sent back to the client.



