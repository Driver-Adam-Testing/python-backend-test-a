# Purpose
This Python script is designed to interact with the Auth0 Management API to manage applications and APIs within an Auth0 tenant. It provides a set of functions to create and delete different types of Auth0 applications, such as Single Page Applications (SPA), Machine-to-Machine (M2M) applications, and APIs. The script also includes functionality to manage roles and permissions, allowing for the assignment of specific permissions to roles for a given API. The script uses the `httpx` library for making HTTP requests and the `auth0` library for interfacing with Auth0's management services.

The script is structured to be a utility or helper module that can be imported and used in other parts of a larger application. It does not define a public API or external interface but rather provides a collection of functions that perform specific tasks related to Auth0 management. Key components include functions for creating and deleting applications and APIs, managing roles, and assigning permissions. The script relies on configuration settings for Auth0 domain and credentials, which are imported from a separate configuration module, ensuring that sensitive information is managed securely.
# Imports and Dependencies

---
- `httpx`
- `auth0.authentication.GetToken`
- `auth0.management.Auth0`
- `config.settings`
- `models.Auth0SpaCreateAppRequest`


# Global Variables

---
### auth0_client 
- **Type**: `Auth0`
- **Description**: The `auth0_client` is an instance of the `Auth0` class, initialized with the domain and an access token obtained through client credentials. It serves as the main interface for interacting with the Auth0 Management API, allowing operations such as creating, deleting, and managing applications and APIs.
- **Use**: This variable is used to perform various management operations on Auth0 resources, such as creating applications, managing connections, and assigning roles and permissions.


---
### domain 
- **Type**: `str`
- **Description**: The `domain` variable is a string that holds the Auth0 domain used for authentication and management API requests. It is initialized with the value of `settings.AUTH0_DOMAIN`, which is expected to be configured in the application's settings.
- **Use**: This variable is used to configure the Auth0 client and token retrieval for API interactions.


---
### get_token 
- **Type**: `GetToken`
- **Description**: The `get_token` variable is an instance of the `GetToken` class, which is initialized with the Auth0 domain, management client ID, and management client secret. This instance is used to obtain authentication tokens from Auth0.
- **Use**: This variable is used to acquire client credentials for accessing the Auth0 Management API.


---
### mgmt_api_audience 
- **Type**: `str`
- **Description**: The `mgmt_api_audience` variable is a string that holds the audience identifier for the Auth0 Management API. This identifier is used to specify the intended recipient of the token when requesting access tokens from Auth0.
- **Use**: This variable is used to obtain a client credentials token for accessing the Auth0 Management API.


---
### mgmt_client_id 
- **Type**: `str`
- **Description**: The `mgmt_client_id` is a string variable that holds the client ID for the Auth0 Management API. It is retrieved from the application settings, specifically from `settings.AUTH0_MGMT_API_CLIENT_ID`. This client ID is used to authenticate and authorize API requests to the Auth0 Management API.
- **Use**: This variable is used to initialize the `GetToken` object for obtaining an access token to interact with the Auth0 Management API.


---
### mgmt_client_secret 
- **Type**: `str`
- **Description**: The `mgmt_client_secret` is a string variable that holds the client secret for the Auth0 Management API. This secret is used in conjunction with the client ID to authenticate and authorize API requests.
- **Use**: This variable is used to obtain a token for accessing the Auth0 Management API by passing it to the `GetToken` class.


---
### token 
- **Type**: `dict`
- **Description**: The `token` variable is a dictionary that holds the access token obtained from the Auth0 authentication service. It is retrieved using the `client_credentials` method of the `GetToken` class, which is initialized with the Auth0 domain, management client ID, and management client secret.
- **Use**: This variable is used to authenticate requests to the Auth0 management API by providing the access token in the authorization header.


# Functions

---
### assign_role_permissions_to_api 
The function assigns specified permissions to a role for a given API in Auth0.
- **Inputs**:
    - `role_name`: The name of the role to which permissions will be assigned.
    - `api_identifier`: The identifier of the API for which permissions are being assigned.
    - `permissions`: A list of permission names to be assigned to the role for the specified API.
- **Control Flow**:
    - Attempt to retrieve the role using the provided role name by calling `get_role_by_name` function.
    - If the role is not found, print an error message and return `False`.
    - Create a list of permission objects, each containing the API identifier and a permission name from the input list.
    - Attempt to add the created permission objects to the role using `auth0_client.roles.add_permissions`.
    - If successful, print a success message and return `True`.
    - If any exception occurs during the process, print an error message and return `False`.
- **Output**:
    - Returns `True` if permissions are successfully assigned, otherwise returns `False`.


---
### create_api_app 
The `create_api_app` function creates an API in Auth0 with specified configurations and assigns permissions to a role for the API.
- **Inputs**:
    - `name`: The name of the API to be created.
    - `identifier`: The unique identifier for the API to be created.
- **Control Flow**:
    - An API payload dictionary is constructed with the provided name and identifier, along with predefined settings such as signing algorithm, token lifetime, and scopes.
    - The API is created using the Auth0 client by passing the payload to `auth0_client.resource_servers.create`.
    - A message is printed to confirm the creation of the API, displaying its name and ID.
    - The identifier is stored in `api_identifier` for further use.
    - A list of admin permissions is defined, which includes specific scopes that match those defined in the API payload.
    - The `assign_role_permissions_to_api` function is called to assign these permissions to the 'Admin' role for the created API.
    - A message is printed to confirm the assignment of permissions to the role for the API.
    - The created API object is returned.
- **Output**:
    - A dictionary representing the created API object, as returned by the Auth0 client.


---
### create_m2m_app 
The `create_m2m_app` function creates a machine-to-machine (M2M) application in Auth0 and authorizes it to call a specified API with predefined scopes.
- **Inputs**:
    - `name`: The name of the M2M application to be created.
    - `identifier`: The API identifier that the M2M application will be authorized to call.
- **Control Flow**:
    - Create a new M2M client using the Auth0 client with the specified name, setting it as a non-interactive application with client credentials grant type and OIDC conformance.
    - Print a confirmation message with the created M2M application's client ID.
    - Define a list of scopes that the M2M application will be authorized to use when calling the specified API.
    - Create a client grant in Auth0 to authorize the M2M application to call the API identified by the `identifier` with the specified scopes.
    - Print a confirmation message indicating the M2M application has been authorized to call the specified API.
    - Return the created M2M application object.
- **Output**:
    - A dictionary representing the created M2M application, including its details such as client ID.


---
### create_spa_web_app 
The `create_spa_web_app` function creates a new single-page application (SPA) in Auth0 and disables the Google OAuth2 connection for it.
- **Inputs**:
    - `create_app`: An instance of `Auth0SpaCreateAppRequest` containing the details required to create the SPA.
- **Control Flow**:
    - The function begins by creating a new SPA client in Auth0 using the `create_app` parameter and stores the result in `spa_app`.
    - It searches for the 'google-oauth2' connection among all available connections in Auth0 and retrieves its ID.
    - A URL is constructed to disable the Google OAuth2 connection for the newly created SPA client.
    - A payload is prepared with the SPA client's ID and a status set to `False`, indicating the connection should be disabled.
    - HTTP headers are set up, including an authorization header with a bearer token.
    - An HTTP PATCH request is made to the constructed URL with the prepared headers and payload to disable the connection.
    - If the request is successful, a success message is printed; otherwise, an error message is printed if an HTTP status error occurs.
    - Finally, the function returns the `spa_app` dictionary containing details of the created SPA.
- **Output**:
    - A dictionary containing details of the newly created SPA application in Auth0.


---
### delete_auth0_api 
The `delete_auth0_api` function attempts to delete an Auth0 API using its API ID and returns a boolean indicating success or failure.
- **Inputs**:
    - `api_id`: A string representing the unique identifier of the Auth0 API to be deleted.
- **Control Flow**:
    - The function tries to delete the Auth0 API by calling `auth0_client.resource_servers.delete(api_id)`.
    - If the deletion is successful, it prints a success message and returns `True`.
    - If an exception occurs during the deletion process, it catches the exception, prints an error message, and returns `False`.
- **Output**:
    - A boolean value indicating whether the Auth0 API was successfully deleted (`True`) or if an error occurred (`False`).


---
### delete_auth0_app 
The `delete_auth0_app` function deletes an Auth0 application using its client ID and returns a boolean indicating success or failure.
- **Inputs**:
    - `client_id`: A string representing the client ID of the Auth0 application to be deleted.
- **Control Flow**:
    - The function attempts to delete the Auth0 application using the provided client ID by calling `auth0_client.clients.delete(client_id)`.
    - If the deletion is successful, it prints a success message and returns `True`.
    - If an exception occurs during the deletion process, it catches the exception, prints an error message, and returns `False`.
- **Output**:
    - A boolean value indicating whether the Auth0 application was successfully deleted (`True`) or if an error occurred (`False`).


---
### get_role_by_name 
The function `get_role_by_name` retrieves a role from Auth0 by its name.
- **Inputs**:
    - `role_name`: A string representing the name of the role to be retrieved.
- **Control Flow**:
    - The function attempts to list all roles using the `auth0_client.roles.list()` method.
    - It iterates over the roles retrieved, checking if any role's name matches the provided `role_name`.
    - If a matching role is found, it returns the role as a dictionary.
    - If no matching role is found, it returns `None`.
    - If an exception occurs during the process, it prints an error message and returns `None`.
- **Output**:
    - A dictionary representing the role if found, otherwise `None`.


