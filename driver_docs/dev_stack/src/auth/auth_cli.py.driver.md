# Purpose
This Python script is a command-line interface (CLI) tool designed to manage authentication with Auth0 using the PKCE (Proof Key for Code Exchange) flow, leveraging FastAPI for the authentication process. It provides narrow functionality focused on user authentication tasks, including logging in, fetching the current user's profile, and logging out. The script uses the `click` library to define a CLI with three commands: `login`, `whoami`, and `logout`. The `login` command initiates the authentication process and stores the received tokens, `whoami` retrieves and displays the user's profile information if logged in, and `logout` clears the stored tokens to log the user out. This script is a concise utility for managing authentication tokens and user sessions in a command-line environment.
# Imports and Dependencies

---
- `json`
- `auth_flow`
- `click`
- `httpx`
- `token_store`


# Functions

---
### cli 
The `cli` function initializes a command-line interface group for authentication operations using FastAPI and Auth0 PKCE.
- **Inputs**:
    - None
- **Control Flow**:
    - The function is decorated with `@click.group()`, indicating it serves as a command group for Click, a Python package for creating command-line interfaces.
    - The function itself does not contain any logic or parameters; it serves as a container for subcommands defined elsewhere in the code.
- **Output**:
    - The function does not return any output; it sets up a command group for further CLI commands.


---
### login 
The `login` function handles user authentication by obtaining and saving tokens from Auth0.
- **Inputs**:
    - None
- **Control Flow**:
    - Call the `auth_flow.login()` function to initiate the login process and retrieve authentication tokens.
    - Pass the retrieved tokens to the `save_tokens` function to store them securely.
    - Display a success message to the user indicating that the login was successful and tokens have been cached.
- **Output**:
    - The function does not return any value; it performs actions related to user login and outputs a success message to the console.


---
### logout 
The `logout` function logs the user out by clearing stored tokens and notifying the user.
- **Inputs**:
    - None
- **Control Flow**:
    - Call the `clear_tokens` function to remove any stored authentication tokens.
    - Use `click.echo` to print a message indicating the user has been logged out.
- **Output**:
    - The function does not return any value; it performs actions to clear tokens and print a message.


---
### whoami 
The `whoami` function retrieves and displays the current user's profile information from Auth0 using stored access tokens.
- **Inputs**:
    - None
- **Control Flow**:
    - Load tokens using the `load_tokens` function.
    - Check if tokens are available; if not, display a message indicating the user is not logged in and return.
    - If tokens are available, set up an authorization header using the access token.
    - Make a GET request to the Auth0 userinfo endpoint using the `httpx` library with the authorization header.
    - Check the response status code; if 200, parse the JSON response and display the user profile information.
    - If the response status code is not 200, display a message indicating the failure to fetch user info.
- **Output**:
    - The function outputs the user's profile information in JSON format if successful, or an error message if not.


