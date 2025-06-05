# Purpose
This Python file is a FastAPI router module that provides API endpoints for user-related operations, specifically focusing on password management and organization retrieval. The code defines two main endpoints: one for changing a user's password (`PUT /password`) and another for retrieving a list of organizations associated with a user (`GET /organizations`). The module uses FastAPI's `APIRouter` to organize these endpoints, making it a part of a larger web application where these functionalities are exposed as part of the API.

The code integrates with an external authentication service, Auth0, through the `Auth0Service` class, which handles the actual logic for changing passwords and listing organizations. The endpoints require user authentication, as indicated by the use of the `UserToken` and the `authorization` header. Logging is implemented to track user actions and errors, providing insights into operations and aiding in debugging. This module is designed to be imported and used within a FastAPI application, contributing specific user management capabilities to the broader system.
# Imports and Dependencies

---
- `logging`
- `fastapi.APIRouter`
- `fastapi.Header`
- `fastapi.HTTPException`
- `app.api.auth.UserToken`
- `app.schemas.user_schema.MessageResponse`
- `app.services.auth0_service.Auth0Service`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module, configured to use the module's name as its logger name. It is used to log messages that are categorized by severity levels, such as debug, info, warning, error, and critical.
- **Use**: This variable is used to log error messages when exceptions occur in the API endpoints.


---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related endpoints for the application, allowing for modular and organized route management.
- **Use**: This variable is used to register and manage HTTP endpoints for password change and organization retrieval functionalities.


# Functions

---
### change_password 
The `change_password` function handles a password reset request for a user by interacting with the Auth0 service.
- **Inputs**:
    - `user`: An instance of `UserToken` representing the user requesting the password change.
    - `authorization`: An optional string from the request header, expected to be a Bearer token for authorization.
- **Control Flow**:
    - Log the initiation of a password reset request with the user's subject information.
    - Extract the access token from the `authorization` header by removing the 'Bearer ' prefix.
    - Instantiate the `Auth0Service` to handle the password change operation.
    - Attempt to change the user's password using the `change_self_password` method of `Auth0Service`, passing the user and access token.
    - If successful, return a message response indicating the password change.
    - If an exception occurs, log the error and raise an HTTP 500 exception indicating the failure to request a password reset.
- **Output**:
    - A `MessageResponse` dictionary containing a message about the password change operation.


---
### get_organizations 
The `get_organizations` function retrieves a list of organizations associated with a user from the Auth0 service.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user making the request.
- **Control Flow**:
    - Logs an informational message indicating a user-requested password reset using the user's subject.
    - Attempts to create an instance of `Auth0Service`.
    - Calls the `list_organizations` method on the `Auth0Service` instance, passing the `user` as an argument, and returns the result.
    - Catches any exceptions that occur during the process, logs an error message, and raises an `HTTPException` with a 500 status code and an error message.
- **Output**:
    - Returns a list of organizations associated with the user, as provided by the `Auth0Service`.


