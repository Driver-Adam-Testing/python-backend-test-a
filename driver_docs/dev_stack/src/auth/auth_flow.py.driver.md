# Purpose
This Python script is designed to facilitate OAuth 2.0 authentication using the PKCE (Proof Key for Code Exchange) extension with Auth0 as the identity provider. It is implemented as a FastAPI application that runs a local server to handle the OAuth callback. The script includes functions to generate a PKCE verifier and challenge pair, initiate the OAuth authorization flow by opening a web browser to the Auth0 authorization endpoint, and handle the callback to capture the authorization code. Once the authorization code is received, it exchanges the code for tokens by making a POST request to the Auth0 token endpoint. The script is structured to be executed as a standalone application, leveraging threading to run the FastAPI server concurrently with the main authentication flow.

The key components of the script include the `generate_pkce_pair` function for creating the PKCE verifier and challenge, the `callback` endpoint to capture the authorization code, and the `get_tokens` function to exchange the code for access and refresh tokens. The `login` function orchestrates the entire process, from generating the PKCE pair to opening the browser for user login and finally retrieving the tokens. This script is primarily intended for use cases where a local application needs to authenticate users via OAuth 2.0, providing a streamlined and automated way to handle the authentication flow without requiring manual intervention beyond the initial login.
# Imports and Dependencies

---
- `base64`
- `hashlib`
- `os`
- `webbrowser`
- `threading.Thread`
- `httpx`
- `uvicorn`
- `fastapi.FastAPI`
- `fastapi.Request`
- `fastapi.responses.HTMLResponse`


# Global Variables

---
### AUTH0_DOMAIN 
- **Type**: `str`
- **Description**: `AUTH0_DOMAIN` is a string variable that holds the domain name for the Auth0 authentication service used in the application. It is set to 'driverai-dev.us.auth0.com', which is likely a specific tenant or environment for the Auth0 service.
- **Use**: This variable is used to construct URLs for making authentication requests to the Auth0 service.


---
### CLIENT_ID 
- **Type**: `str`
- **Description**: `CLIENT_ID` is a string variable that holds the client identifier used for authentication with the Auth0 service. It is a unique identifier assigned to the application by the Auth0 platform.
- **Use**: This variable is used in the OAuth2 authentication flow to identify the client application when requesting tokens from the Auth0 authorization server.


---
### ORG_ID 
- **Type**: `str`
- **Description**: `ORG_ID` is a string variable that holds the identifier for an organization, specifically 'org_s76pU1v8LAYhTOWB'. This identifier is likely used to associate API requests or authentication processes with a specific organization within the Auth0 authentication framework.
- **Use**: This variable is used to specify the organization in the authentication process, although it is currently commented out in the `login` function.


---
### REDIRECT_URI 
- **Type**: `str`
- **Description**: `REDIRECT_URI` is a string variable that holds the URL to which the authorization server will redirect the user after they have authenticated. In this case, it is set to 'http://localhost:4001/callback', which is a local endpoint for handling the callback from the authentication process.
- **Use**: This variable is used in the OAuth2 authentication flow to specify the callback URL where the authorization code will be sent.


---
### SCOPES 
- **Type**: `string`
- **Description**: The `SCOPES` variable is a string that defines the OAuth 2.0 scopes requested during the authentication process. It includes the scopes 'openid', 'profile', 'email', and 'offline_access', which are used to request specific permissions from the user.
- **Use**: This variable is used in the `login` function to specify the scopes when constructing the authorization URL for the OAuth 2.0 flow.


---
### app 
- **Type**: `FastAPI`
- **Description**: The `app` variable is an instance of the FastAPI class, which is used to create a web application. FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
- **Use**: This variable is used to define the web application and its routes, such as the '/callback' endpoint, which handles OAuth2 callback requests.


---
### auth_code_container 
- **Type**: `dict`
- **Description**: The `auth_code_container` is a dictionary used to store the authorization code received from the OAuth2 callback endpoint. It acts as a temporary storage to hold the code until it is used to request tokens.
- **Use**: This variable is used to store the authorization code received from the callback URL, which is then used to obtain access tokens.


# Functions

---
### callback 
The `callback` function handles the OAuth callback by extracting the authorization code from the request and storing it for further processing.
- **Inputs**:
    - `request`: An instance of `Request` from FastAPI, representing the incoming HTTP request to the callback endpoint.
- **Control Flow**:
    - Extract the 'code' parameter from the query parameters of the request.
    - Check if the 'code' is present; if not, return an HTML response indicating the absence of the code with a 400 status code.
    - If the 'code' is present, store it in the `auth_code_container` dictionary under the key 'code'.
    - Return an HTML response indicating a successful login.
- **Output**:
    - An HTML response indicating either a successful login or an error due to the absence of the authorization code.


---
### generate_pkce_pair 
The `generate_pkce_pair` function generates a PKCE (Proof Key for Code Exchange) verifier and challenge pair for OAuth 2.0 authentication.
- **Inputs**:
    - None
- **Control Flow**:
    - Generate a random 40-byte string using `os.urandom` and encode it in a URL-safe base64 format, removing any trailing '=' characters to create the `verifier`.
    - Hash the `verifier` using SHA-256, encode the hash in a URL-safe base64 format, and remove any trailing '=' characters to create the `challenge`.
    - Return the `verifier` and `challenge` as a tuple.
- **Output**:
    - A tuple containing the PKCE verifier and challenge strings.


---
### get_tokens 
The `get_tokens` function exchanges an authorization code for access tokens using the OAuth 2.0 protocol.
- **Inputs**:
    - `code`: The authorization code received from the OAuth 2.0 authorization server.
    - `verifier`: The code verifier used in the PKCE (Proof Key for Code Exchange) flow to enhance security.
- **Control Flow**:
    - A payload dictionary is created containing the grant type, client ID, authorization code, redirect URI, and code verifier.
    - Headers are set to indicate the content type as 'application/x-www-form-urlencoded'.
    - An HTTP POST request is made to the Auth0 domain's token endpoint with the payload and headers.
    - The response status is checked, and an exception is raised if the request was unsuccessful.
    - The JSON content of the response is returned, which contains the access tokens.
- **Output**:
    - A JSON object containing the access tokens and other related information from the OAuth 2.0 token endpoint.


---
### login 
The `login` function initiates an OAuth2 authorization code flow with PKCE, opens a web browser for user login, and retrieves access tokens upon successful authentication.
- **Inputs**:
    - None
- **Control Flow**:
    - Generate a PKCE verifier and challenge pair using `generate_pkce_pair`.
    - Construct the authorization URL with necessary parameters including client ID, redirect URI, scopes, and the PKCE challenge.
    - Open the constructed URL in the default web browser to prompt the user for login.
    - Start a background thread to run a local server using `run_server` to handle the callback from the authorization server.
    - Enter a loop that waits until the authorization code is stored in `auth_code_container`.
    - Once the authorization code is received, call `get_tokens` with the code and verifier to exchange them for access tokens.
- **Output**:
    - Returns the access tokens obtained from the authorization server after successful login and code exchange.


---
### run_server 
The `run_server` function starts a Uvicorn server to host a FastAPI application on localhost with specific configurations.
- **Inputs**:
    - None
- **Control Flow**:
    - The function calls `uvicorn.run()` to start the server.
    - It specifies the FastAPI application `app` to be run.
    - The server is configured to run on host `127.0.0.1` and port `4001`.
    - The log level is set to `critical`, which suppresses info and debug logs.
    - Access logs are disabled by setting `access_log` to `False`.
- **Output**:
    - The function does not return any value; it starts a server process.


