
## Files
- **[auth0_device_flow.py](auth/auth0_device_flow.py.driver.md)**: The `auth0_device_flow.py` file implements an Auth0 device flow authenticator that manages device authorization, token retrieval, and caching for a client application.
- **[auth_cli.py](auth/auth_cli.py.driver.md)**: The `auth_cli.py` file implements a command-line interface for authentication using FastAPI and Auth0 with PKCE, providing commands for login, fetching user profile, and logout.
- **[auth_flow.py](auth/auth_flow.py.driver.md)**: The `auth_flow.py` file implements an authentication flow using FastAPI and Auth0, including generating PKCE pairs, handling callback requests, and obtaining tokens.
- **[auth_server.py](auth/auth_server.py.driver.md)**: The `auth_server.py` file implements an authentication server using FastAPI and Auth0, facilitating user login via a browser and handling the exchange of authorization codes for tokens.
- **[cli2.py](auth/cli2.py.driver.md)**: The `cli2.py` file implements a command-line interface for authentication using Auth0's device flow, providing commands to log in, check the current user, and log out.
- **[token_store.py](auth/token_store.py.driver.md)**: The `token_store.py` file provides functions to save, load, and clear authentication tokens stored in a JSON file located in the user's home directory.
