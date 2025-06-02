# Purpose
This Python file is a middleware and authentication module designed for a FastAPI application. It provides functionality for handling JSON Web Token (JWT) authentication, specifically integrating with Auth0 for token verification. The code defines a middleware class, `AuthMiddleware`, which intercepts HTTP requests to enforce authentication and authorization based on JWTs. It uses the `HTTPBearer` security scheme to extract and verify tokens from the `Authorization` header of incoming requests. The middleware allows certain paths to bypass authentication, as specified in the `UNPROTECTED_PATHS` list, while other requests require a valid token.

The module also defines data models using Pydantic for representing user and machine-to-machine (M2M) token payloads, encapsulating details such as user ID, organization information, and permissions. It provides utility functions to retrieve and verify JWTs, extract token payloads, and enforce permission checks. The `require_permission` function is a key component that ensures users have the necessary permissions to access specific resources, raising an HTTP 403 error if permissions are insufficient. This file is intended to be a reusable component within a FastAPI application, providing a robust authentication and authorization framework that can be easily integrated into various endpoints.
# Imports and Dependencies

---
- `json`
- `collections.abc.Callable`
- `typing.Annotated`
- `typing.Any`
- `urllib.request.urlopen`
- `jwt`
- `fastapi.Depends`
- `fastapi.HTTPException`
- `fastapi.Request`
- `fastapi.Response`
- `fastapi.responses.JSONResponse`
- `fastapi.security.HTTPAuthorizationCredentials`
- `fastapi.security.HTTPBearer`
- `jwt.PyJWTError`
- `jwt.algorithms.RSAAlgorithm`
- `pydantic.BaseModel`
- `pydantic.Field`
- `shared.utils.decorators.expiring_cache`
- `starlette.middleware.base.BaseHTTPMiddleware`
- `app.core.config.settings`


# Global Variables

---
### ALGORITHMS 
- **Type**: `list`
- **Description**: The `ALGORITHMS` variable is a list containing a single string, "RS256". This string represents the RSA SHA-256 algorithm, which is a cryptographic algorithm used for signing and verifying JSON Web Tokens (JWTs).
- **Use**: This variable is used in the `verify_token` function to specify the algorithm that should be used to decode and verify JWTs.


---
### CONTENT_EDITOR 
- **Type**: `str`
- **Description**: The `CONTENT_EDITOR` variable is a string that represents a specific permission level or role within the application, specifically related to content editing capabilities. It is used as a constant to check if a user has the 'content:editor' permission, which likely allows them to perform editing operations on content within the system.
- **Use**: This variable is used to define and check for the 'content:editor' permission in the application's permission management system.


---
### CONTENT_READONLY 
- **Type**: `str`
- **Description**: `CONTENT_READONLY` is a string variable that holds the value 'content:readonly'. It is used to represent a specific permission level within the application, likely related to read-only access to content.
- **Use**: This variable is used to define a permission dependency for read-only access to content in the application.


---
### ContentEditorPermission 
- **Type**: `Depends`
- **Description**: `ContentEditorPermission` is a dependency that ensures a user has the 'content:editor' permission. It is created using the `Depends` function, which wraps the `require_permission` function with the `CONTENT_EDITOR` permission string.
- **Use**: This variable is used to enforce that a user has the necessary 'content:editor' permission to access certain routes or perform specific actions in the application.


---
### ContentReadonlyPermission 
- **Type**: `Depends`
- **Description**: `ContentReadonlyPermission` is a dependency that ensures a user has the 'content:readonly' permission. It is created using the `Depends` function, which wraps the `require_permission` function with the 'content:readonly' permission string.
- **Use**: This variable is used to enforce that a user has read-only access to content by checking their permissions.


---
### GIT_PROVIDER_MANAGER 
- **Type**: `str`
- **Description**: `GIT_PROVIDER_MANAGER` is a string constant that represents a specific permission level or role related to managing a Git provider. It is used within the application to check if a user has the necessary permissions to perform management tasks related to Git providers.
- **Use**: This variable is used to define a permission dependency for routes or functions that require Git provider management capabilities.


---
### GitProviderManagerPermission 
- **Type**: `Depends`
- **Description**: `GitProviderManagerPermission` is a dependency injection that ensures a user has the 'git_provider:management' permission. It is created using the `Depends` function from FastAPI, which calls the `require_permission` function with the `GIT_PROVIDER_MANAGER` constant as an argument.
- **Use**: This variable is used to enforce permission checks for routes or operations that require 'git_provider:management' access.


---
### M2MToken 
- **Type**: `Annotated[M2M, Depends(get_current_m2m)]`
- **Description**: `M2MToken` is an annotated type that represents a machine-to-machine (M2M) token, which is used for authentication and authorization in a FastAPI application. It is based on the `M2M` Pydantic model and is dependent on the `get_current_m2m` function to retrieve the current M2M token payload from the request. This token is used to identify and authorize machine-to-machine interactions without a user context.
- **Use**: `M2MToken` is used to authenticate and authorize machine-to-machine interactions by providing a structured representation of the M2M token payload.


---
### ORG_MANAGER 
- **Type**: `string`
- **Description**: The `ORG_MANAGER` variable is a string constant that represents a specific permission level or role within the application, specifically for managing organizational aspects. It is used to define access control and permissions for users who need to perform management tasks related to organizations.
- **Use**: This variable is used in the `require_permission` function to check if a user has the 'organization:management' permission.


---
### OrgManagerPermission 
- **Type**: `Depends`
- **Description**: `OrgManagerPermission` is a dependency that ensures a user has the 'organization:management' permission. It is created using the `Depends` function, which wraps the `require_permission` function with the `ORG_MANAGER` permission string.
- **Use**: This variable is used to enforce that a user has the necessary permissions to perform organization management tasks by checking their token payload for the 'organization:management' permission.


---
### SUBSCRIPTION_MANAGER 
- **Type**: `str`
- **Description**: `SUBSCRIPTION_MANAGER` is a string variable that holds the value 'subscription:management'. It is used as a permission identifier within the application.
- **Use**: This variable is used to define a specific permission level required for managing subscriptions, which can be checked against a user's permissions to authorize access to subscription management features.


---
### SubscriptionManagerPermission 
- **Type**: `Depends`
- **Description**: `SubscriptionManagerPermission` is a dependency that ensures a user has the 'subscription:management' permission. It is created using the `Depends` function, which wraps the `require_permission` function with the `SUBSCRIPTION_MANAGER` constant as an argument.
- **Use**: This variable is used to enforce permission checks for subscription management operations in the application.


---
### UNPROTECTED_PATHS 
- **Type**: `list`
- **Description**: `UNPROTECTED_PATHS` is a list of URL paths that do not require authentication in the application. These paths are accessible without a valid token, allowing users to access certain endpoints like login, health checks, and documentation without authentication.
- **Use**: This variable is used in the `AuthMiddleware` class to determine if a request should bypass authentication checks based on the request's URL path.


---
### USAGE_CREDITOR 
- **Type**: `str`
- **Description**: `USAGE_CREDITOR` is a string constant that represents a specific permission level related to usage credit management within the application. It is used to define and check permissions for users who need to manage usage credits.
- **Use**: This variable is used in the `require_permission` function to create a dependency that checks if a user has the 'usage_credit:management' permission.


---
### UsageCreditPermission 
- **Type**: `Depends`
- **Description**: `UsageCreditPermission` is a dependency that checks if a user has the 'usage_credit:management' permission. It is created using the `Depends` function with the `require_permission` function, which ensures that the user has the necessary permission to manage usage credits.
- **Use**: This variable is used to enforce permission checks in routes or functions that require 'usage_credit:management' access.


---
### UserToken 
- **Type**: `Annotated[User, Depends(get_current_user)]`
- **Description**: `UserToken` is an annotated type that represents a dependency injection for obtaining the current user in the application. It uses the `Depends` function to call `get_current_user`, which retrieves a `User` object based on the token payload extracted from the request. The `User` object contains various fields such as organization ID, user ID, email, and permissions, which are essential for user authentication and authorization.
- **Use**: This variable is used to inject the current authenticated user into FastAPI endpoints, allowing access to user-specific data and permissions.


---
### audience 
- **Type**: `list[str] | str`
- **Description**: The `audience` variable is a field in the `User` and `M2M` classes, represented as either a list of strings or a single string. It is used to specify the intended recipients of the token, often referred to as the 'aud' claim in JWTs.
- **Use**: This variable is used to validate that the token is intended for the correct audience during the token verification process.


---
### authorized_party 
- **Type**: `str`
- **Description**: The `authorized_party` variable is a string field in the `User` and `M2M` Pydantic models, which is aliased from the 'azp' claim in a JWT token. It represents the party to which the token was issued, typically used to identify the client application that requested the token.
- **Use**: This variable is used to store and access the 'azp' claim from a JWT token within the `User` and `M2M` models.


---
### email 
- **Type**: `str`
- **Description**: The `email` variable is a field within the `User` class, which is a Pydantic model. It represents the email address of a user and is mapped from the `user_email` key in the token payload.
- **Use**: This variable is used to store and access the email address of a user within the `User` model, typically for authentication and authorization purposes.


---
### expiration 
- **Type**: `int`
- **Description**: The `expiration` variable is an integer field in the `User` and `M2M` classes, representing the expiration time of a token. It is typically expressed as a Unix timestamp, indicating the exact time when the token will no longer be valid.
- **Use**: This variable is used to determine the validity period of a token, ensuring that it is not used beyond its expiration time.


---
### full_name 
- **Type**: `str`
- **Description**: The `full_name` variable is a field in the `User` class, which is a Pydantic model. It represents the full name of a user and is mapped from the `user_full_name` key in the token payload.
- **Use**: This variable is used to store and access the full name of a user within the `User` model, typically extracted from a token payload.


---
### issued_at 
- **Type**: `int`
- **Description**: The `issued_at` variable is an integer field in the `User` and `M2M` classes, representing the time at which the token was issued. It is typically expressed as a Unix timestamp, which is the number of seconds since January 1, 1970 (UTC).
- **Use**: This variable is used to track when a token was issued, which is important for validating the token's freshness and authenticity.


---
### issuer 
- **Type**: `str`
- **Description**: The `issuer` variable is a string field in the `User` and `M2M` classes, represented by the alias 'iss'. It typically contains the URL of the entity that issued the token, such as an authentication server or identity provider.
- **Use**: This variable is used to verify the origin of a token, ensuring it was issued by a trusted source.


---
### organization_display_name 
- **Type**: `str`
- **Description**: The `organization_display_name` is a string field in the `User` class, which is a Pydantic model. It represents the display name of the organization associated with the user.
- **Use**: This variable is used to store and retrieve the display name of the organization for a user, typically for display purposes in user interfaces or logs.


---
### organization_id 
- **Type**: `str`
- **Description**: The `organization_id` is a string field within the `User` class, which is a Pydantic model. It represents the unique identifier for an organization associated with a user.
- **Use**: This variable is used to store and access the organization ID for a user, typically for authentication and authorization purposes.


---
### organization_name 
- **Type**: `str`
- **Description**: The `organization_name` variable is a field within the `User` class, which is a Pydantic model. It represents the display name of the organization associated with a user.
- **Use**: This variable is used to store and retrieve the display name of the organization for a user, as part of the user's token payload.


---
### permissions 
- **Type**: `list[str]`
- **Description**: The `permissions` variable is a list of strings that represents the permissions assigned to a user. It is part of the `User` class, which models the user data extracted from a token payload.
- **Use**: This variable is used to check if a user has the necessary permissions to access certain resources or perform specific actions within the application.


---
### scope 
- **Type**: `str`
- **Description**: The `scope` variable is a string field within the `User` class, which is a Pydantic model. It represents the scope of access or permissions granted to a user, as defined in the token payload.
- **Use**: This variable is used to store and retrieve the scope of access for a user, which is part of the token payload in authentication processes.


---
### security 
- **Type**: `HTTPBearer`
- **Description**: The `security` variable is an instance of the `HTTPBearer` class from FastAPI's security module. This class is used to handle HTTP Bearer authentication, which is a token-based authentication scheme. It is typically used to secure API endpoints by requiring a token to be included in the Authorization header of HTTP requests.
- **Use**: The `security` variable is used as a dependency in FastAPI route handlers to enforce Bearer token authentication.


---
### subject 
- **Type**: `str`
- **Description**: The `subject` variable is a string field in the `User` and `M2M` classes, which is an alias for the 'sub' claim in a JWT token. It represents the subject of the token, typically a unique identifier for the user or machine-to-machine entity.
- **Use**: This variable is used to map the 'sub' claim from a JWT token to the `subject` field in the `User` and `M2M` data models.


---
### user_id 
- **Type**: `str`
- **Description**: The `user_id` variable is a field within the `User` class, which is a Pydantic model. It represents the unique identifier for a user, typically mapped from the 'sub' claim in a JWT token.
- **Use**: This variable is used to store and access the unique identifier of a user within the application, particularly when handling authentication and authorization processes.


# Classes

---
### AuthMiddleware 
- **Type**: `class`
- **Description**: The `AuthMiddleware` class is a custom middleware for handling authentication in a FastAPI application. It extends the `BaseHTTPMiddleware` class and overrides the `dispatch` method to check for the presence of a valid 'Authorization' header in incoming requests. If the request method is not in the list of unprotected paths or is not an OPTIONS request, it verifies the token using the `verify_token` function. If the token is valid, it stores the token payload in the request state; otherwise, it returns a 401 Unauthorized response.
- **Inherits From**:
    - BaseHTTPMiddleware

**Methods**

---
#### AuthMiddleware.dispatch
The `dispatch` function is an asynchronous middleware method that handles authentication by verifying JWT tokens for protected routes in a FastAPI application.
- **Inputs**:
    - `request`: An instance of `Request` representing the incoming HTTP request.
    - `call_next`: A callable that takes a `Request` and returns a `Response`, used to pass the request to the next middleware or endpoint.
- **Control Flow**:
    - Check if the request method is 'GET' or 'POST' and the URL path is in `UNPROTECTED_PATHS`, or if the method is 'OPTIONS'.
    - If the request is unprotected, bypass authentication and proceed to the next middleware or endpoint.
    - If the request is protected, retrieve the 'Authorization' header from the request.
    - Check if the 'Authorization' header is missing or does not start with 'Bearer '; if so, return a 401 Unauthorized JSON response with an error message.
    - Extract the token from the 'Authorization' header by removing the 'Bearer ' prefix.
    - Attempt to verify the token using the `verify_token` function, which decodes the JWT and checks its validity.
    - If token verification fails, return a 401 Unauthorized JSON response with an error message.
    - If token verification succeeds, store the token payload in `request.state.token_payload`.
    - Call the `call_next` function with the request to continue processing and obtain the response.
    - Return the response obtained from `call_next`.
- **Output**:
    - The function returns a `JSONResponse` or `Response` object, which is the result of either an authentication failure or the next middleware/endpoint's response.



---
### M2M 
- **Type**: `class`
- **Members**:
    - `issuer`: Represents the issuer of the token, aliased as 'iss'.
    - `subject`: Represents the subject of the token, aliased as 'sub'.
    - `audience`: Represents the audience of the token, aliased as 'aud', and can be a list of strings or a single string.
    - `issued_at`: Represents the time at which the token was issued, aliased as 'iat'.
    - `expiration`: Represents the expiration time of the token, aliased as 'exp'.
    - `authorized_party`: Represents the party authorized to use the token, aliased as 'azp'.
- **Description**: The M2M class is a Pydantic model that defines the structure of a machine-to-machine (M2M) token, which includes fields for issuer, subject, audience, issued time, expiration time, and authorized party. Each field is associated with an alias that corresponds to standard JWT claims, facilitating the validation and parsing of M2M tokens in authentication processes.
- **Inherits From**:
    - BaseModel


---
### User 
- **Type**: `class`
- **Members**:
    - `organization_id`: Represents the ID of the organization the user belongs to.
    - `organization_display_name`: Stores the display name of the organization.
    - `user_id`: Holds the unique identifier for the user.
    - `issuer`: Indicates the issuer of the token.
    - `subject`: Represents the subject of the token, typically the user ID.
    - `audience`: Specifies the audience for which the token is intended.
    - `issued_at`: Records the timestamp when the token was issued.
    - `expiration`: Indicates the timestamp when the token will expire.
    - `scope`: Defines the scope of access granted by the token.
    - `organization_name`: Stores the name of the organization.
    - `authorized_party`: Identifies the party authorized to use the token.
    - `permissions`: Lists the permissions granted to the user.
    - `email`: Contains the email address of the user.
    - `full_name`: Holds the full name of the user.
- **Description**: The `User` class is a Pydantic model that represents a user entity with various attributes related to authentication and authorization. It includes fields for organization details, user identification, token metadata, and permissions. The class uses Pydantic's `Field` to define aliases for JSON serialization and deserialization, ensuring compatibility with external systems that may use different naming conventions.
- **Inherits From**:
    - BaseModel


# Functions

---
### get_current_m2m 
The `get_current_m2m` function returns an M2M object if the token payload does not contain a userId, otherwise it returns None.
- **Inputs**:
    - `credentials`: An instance of HTTPAuthorizationCredentials, which is automatically provided by FastAPI's dependency injection system using the HTTPBearer security scheme.
    - `token_payload`: A dictionary containing the token payload, which is also provided by FastAPI's dependency injection system through the get_token_payload function.
- **Control Flow**:
    - The function checks if the 'userId' key is present in the token_payload dictionary.
    - If 'userId' is not present, it creates and returns an M2M object using the token_payload data.
    - If 'userId' is present, it returns None.
- **Output**:
    - The function returns an M2M object if the token payload does not contain a 'userId', otherwise it returns None.


---
### get_current_user 
The `get_current_user` function retrieves the current user from the token payload if a user ID is present.
- **Inputs**:
    - `credentials`: An instance of `HTTPAuthorizationCredentials` obtained via dependency injection using FastAPI's `Depends` with the `security` object, which is an instance of `HTTPBearer`.
    - `token_payload`: A dictionary obtained via dependency injection using FastAPI's `Depends` with the `get_token_payload` function, which contains the token payload data.
- **Control Flow**:
    - The function checks if the 'userId' key is present in the `token_payload` dictionary.
    - If 'userId' is present, it creates and returns a `User` object using the data from `token_payload`.
    - If 'userId' is not present, the function returns `None`.
- **Output**:
    - The function returns a `User` object if a user ID is present in the token payload, otherwise it returns `None`.


---
### get_jwks 
The `get_jwks` function retrieves and returns the JSON Web Key Set (JWKS) from the Auth0 API, caching the result for an hour to reduce API calls.
- **Inputs**:
    - None
- **Control Flow**:
    - Constructs the URL for the JWKS endpoint using the Auth0 domain from the settings.
    - Opens a connection to the JWKS URL and retrieves the response.
    - Parses the response content as JSON and returns it as a dictionary.
- **Output**:
    - A dictionary representing the JSON Web Key Set (JWKS) retrieved from the Auth0 API.


---
### get_rsa_key 
The `get_rsa_key` function retrieves an RSA key from a JSON Web Key Set (JWKS) based on a specified key ID (kid).
- **Inputs**:
    - `jwks`: A dictionary representing the JSON Web Key Set, which contains a list of keys.
    - `kid`: A string representing the key ID used to identify the specific key to retrieve from the JWKS.
- **Control Flow**:
    - Iterates over each key in the 'keys' list within the provided JWKS dictionary.
    - Checks if the 'kid' of the current key matches the provided 'kid'.
    - If a match is found, constructs and returns a dictionary containing the key type ('kty'), key ID ('kid'), usage ('use'), modulus ('n'), and exponent ('e') of the matching key.
    - If no matching key is found after iterating through all keys, returns an empty dictionary.
- **Output**:
    - A dictionary containing the RSA key details if a matching key is found, otherwise an empty dictionary.


---
### get_token_payload 
The `get_token_payload` function retrieves the token payload from the request's state after it has been validated.
- **Inputs**:
    - `request`: A `Request` object from which the token payload is retrieved.
- **Control Flow**:
    - The function directly accesses the `token_payload` attribute from the `state` of the `request` object.
    - It assumes that the `token_payload` has already been populated and validated by prior middleware or function calls.
- **Output**:
    - A dictionary representing the token payload stored in the request's state.


---
### permission_dependency 
The `permission_dependency` function checks if a user has a specific permission and raises an HTTP exception if not.
- **Inputs**:
    - `user`: A dictionary representing the current user, obtained via dependency injection from `get_current_user`.
    - `token_payload`: A dictionary containing the token payload, obtained via dependency injection from `get_token_payload`.
- **Control Flow**:
    - Retrieve the list of permissions from the `token_payload` dictionary using the key 'permissions'.
    - Check if the specified `permission` is not in the retrieved permissions list.
    - If the `permission` is not found, raise an `HTTPException` with a 403 status code and a detail message indicating insufficient permissions.
    - If the `permission` is found, return `True`.
- **Output**:
    - Returns `True` if the user has the required permission; otherwise, raises an `HTTPException` with a 403 status code.


---
### require_permission 
The `require_permission` function returns a dependency function that checks if a user has a specific permission from their token payload.
- **Inputs**:
    - `permission`: A string representing the required permission to be checked against the user's token payload.
- **Control Flow**:
    - Defines an inner function `permission_dependency` that takes `user` and `token_payload` as dependencies, which are resolved using FastAPI's `Depends` mechanism.
    - Retrieves the list of permissions from the `token_payload` dictionary using the key 'permissions'.
    - Checks if the specified `permission` is not in the retrieved permissions list.
    - If the permission is not found, raises an `HTTPException` with a 403 status code indicating insufficient permissions.
    - If the permission is found, returns `True`.
- **Output**:
    - A callable function `permission_dependency` that checks for the specified permission in the user's token payload and returns `True` if the permission is present, otherwise raises an HTTPException.


---
### verify_token 
The `verify_token` function validates a JWT token by checking its signature and claims against a public key obtained from a JWKS endpoint.
- **Inputs**:
    - `token`: A JSON Web Token (JWT) string that needs to be verified.
- **Control Flow**:
    - Retrieve the unverified header from the provided JWT token using `jwt.get_unverified_header`.
    - Call `get_jwks` to obtain the JSON Web Key Set (JWKS) from the Auth0 endpoint.
    - Use `get_rsa_key` to find the RSA key from the JWKS that matches the 'kid' (key ID) from the unverified header.
    - If no matching RSA key is found, raise an HTTP 401 Unauthorized exception with a detail message.
    - Convert the RSA key to a public key using `RSAAlgorithm.from_jwk`.
    - Attempt to decode the JWT token using the public key, specified algorithms, audience, and issuer.
    - If decoding fails due to a `PyJWTError`, raise an HTTP 401 Unauthorized exception with a detail message.
- **Output**:
    - A dictionary containing the decoded payload of the JWT if verification is successful.


