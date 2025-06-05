# Purpose
This Python file is a FastAPI application that provides a comprehensive API for managing Git provider applications and their installations. It is designed to handle interactions with Git providers such as GitHub and GitLab, facilitating operations like creating, deleting, and authorizing Git provider apps, managing group access tokens, and handling webhooks for events like push notifications and installation modifications. The file imports various modules and dependencies, including database models, authentication and session management utilities, and AWS configurations for secret management, indicating its integration with a broader system architecture.

The code defines several API endpoints using FastAPI's `APIRouter`, each serving a specific function related to Git provider app management. These endpoints include operations for fetching and creating Git provider apps, managing installations, handling authorization callbacks, and processing webhook events. The file also includes utility functions for verifying signatures and handling specific Git provider events, ensuring secure and efficient communication with external Git services. The use of Pydantic models for request and response validation, along with detailed logging and error handling, highlights the file's focus on robustness and maintainability. Overall, this file serves as a critical component in a larger system that integrates with Git providers to manage application installations and respond to repository events.
# Imports and Dependencies

---
- `base64`
- `hashlib`
- `hmac`
- `json`
- `logging`
- `itertools`
- `uuid`
- `modal`
- `database.models_v1`
- `database.models_v2`
- `database.models_v2_enums`
- `fastapi`
- `fastapi.responses`
- `pydantic`
- `shared.interfaces.aws_client_config`
- `shared.secret_management.aws_secret_management`
- `sqlmodel`
- `app.api.auth`
- `app.api.session`
- `app.core.config`
- `app.git_providers.utils.errors`
- `app.repositories.git_provider_repository`
- `app.repositories.github_app_installations_repository`
- `app.schemas.git_provider_schema`
- `app.schemas.secret_management_schema`
- `app.services.gitlab_provider_service`
- `app.utils.aws_s3`
- `app.utils.aws_secrets_manager`
- `app.utils.gh_ops`


# Global Variables

---
### NO_OS_DRIVER_BRANCH 
- **Type**: `str`
- **Description**: The `NO_OS_DRIVER_BRANCH` variable is a string that holds the name of a specific branch, 'staging/docs', in a GitHub repository. This branch is likely used for documentation purposes related to the 'no-OS' project within the 'analogdevicesinc' GitHub organization.
- **Use**: This variable is used to specify the branch name when interacting with the 'no-OS' repository, particularly for operations that require branch-specific actions.


---
### NO_OS_GH_ORG 
- **Type**: ``str``
- **Description**: The `NO_OS_GH_ORG` variable is a string that holds the name of the GitHub organization 'analogdevicesinc'. This organization is likely associated with repositories related to Analog Devices Inc.
- **Use**: This variable is used to identify the GitHub organization when performing operations related to the 'no-OS' repository, such as fetching commit hashes or verifying repository details.


---
### NO_OS_REPO_NAME 
- **Type**: `str`
- **Description**: The `NO_OS_REPO_NAME` variable is a string that holds the name of a specific GitHub repository, which in this case is 'no-OS'. This repository is likely associated with the organization 'analogdevicesinc', as indicated by the related variable `NO_OS_GH_ORG`. The repository name is used in various parts of the code to identify and interact with this specific repository, particularly in operations related to GitHub events and repository management.
- **Use**: This variable is used to identify and reference the 'no-OS' repository in GitHub-related operations and logic within the application.


---
### aws_config 
- **Type**: `AWSClientConfig`
- **Description**: The `aws_config` variable is an instance of the `AWSClientConfig` class, which is used to configure AWS client settings. It is initialized with specific AWS credentials and region information, such as `region_name`, `aws_access_key_id`, and `aws_secret_access_key`, which are retrieved from the application's settings.
- **Use**: This variable is used to provide AWS configuration details for various AWS-related operations throughout the application, such as secret management and repository cloning.


---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module in Python. It is configured to handle logging messages for the application, allowing for the recording of events, errors, and other informational messages.
- **Use**: This variable is used throughout the application to log messages, including errors and informational events, which can be helpful for debugging and monitoring the application's behavior.


---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a set of routes for the application, allowing for modular and organized route management.
- **Use**: This variable is used to register and manage API endpoints for the application, facilitating the handling of HTTP requests and responses.


---
### status 
- **Type**: `module`
- **Description**: The `status` variable is imported from the `fastapi` module and is used to provide HTTP status codes for responses. It is a part of the FastAPI framework, which simplifies the process of returning HTTP status codes in API responses.
- **Use**: This variable is used to specify HTTP status codes in JSONResponse objects throughout the FastAPI application.


# Classes

---
### OkResponse 
- **Type**: `class`
- **Members**:
    - `status`: A string indicating the status of the response, defaulting to 'OK'.
- **Description**: The `OkResponse` class is a simple response model that inherits from `BaseModel` and is used to validate and return a standard response when performing a health check. It contains a single attribute, `status`, which is a string set to "OK" by default, indicating that the health check was successful.
- **Inherits From**:
    - BaseModel


# Functions

---
### _extract_body_and_headers 
The function asynchronously extracts the body and headers from a FastAPI request and returns them in a dictionary.
- **Inputs**:
    - `request`: A FastAPI Request object from which the body and headers are to be extracted.
- **Control Flow**:
    - The function awaits the body of the request to be read as bytes.
    - It then parses the body bytes into a JSON object using json.loads.
    - Finally, it returns a dictionary containing the raw body bytes, the parsed JSON body, and the request headers.
- **Output**:
    - A dictionary containing the raw body bytes, the JSON-parsed body, and the request headers.


---
### add_group_access_token 
The `add_group_access_token` function adds a group access token to a specified application for the current user's organization and handles potential errors.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A string representing the ID of the application to which the group access token is to be added.
    - `gat`: An instance of `GroupAccessToken` representing the group access token to be added.
- **Control Flow**:
    - The function attempts to install the group access token by calling `install_group_access_token` with the provided session, organization ID, application ID, group access token, and AWS configuration.
    - If the installation is not successful (i.e., `install` is `None` or `False`), an `HTTPException` with a 404 status code is raised, indicating that the installation was not found.
    - If the installation is successful, a `JSONResponse` with a 200 status code and a message indicating that the token was added is returned.
    - If a `GitProviderAccessTokenError` is raised during the process, it is caught, logged, and an `HTTPException` with a 500 status code and a message indicating an invalid token is raised.
- **Output**:
    - The function returns a `JSONResponse` indicating the success or failure of adding the group access token, with appropriate HTTP status codes and messages.


---
### clone_git_provider_repo 
The `clone_git_provider_repo` function clones a specified Git repository and returns a URL for downloading the analysis of the repository.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A string representing the ID of the application associated with the Git repository.
    - `repo`: An instance of `GitRepository` representing the Git repository to be cloned.
- **Control Flow**:
    - Constructs an `upload_key` string using the organization ID from `current_user` and the repository name from `repo`.
    - Determines the `bucket_name` based on the `settings.USE_LEGACY_DROPZONE` configuration.
    - Calls the `clone_git_repository` function with the session, user and organization IDs, application ID, repository, upload key, bucket name, and AWS configuration to clone the repository and get the download URL.
    - Returns a `JSONResponse` with a status code of 202 (Accepted) and a content dictionary containing the `download_url`.
- **Output**:
    - A `JSONResponse` object with a status code of 202 and a content dictionary containing the `download_url` for the cloned repository analysis.


---
### clone_repo 
The `clone_repo` function clones a GitHub repository for a given user and organization, verifies access, and uploads the repository to a specified location.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current user, including their organization ID and user ID.
    - `provider`: A string indicating the provider of the repository, expected to be 'github'.
    - `repo`: An instance of `GitRepository` containing details about the repository to be cloned, including its name, organization, and metadata.
- **Control Flow**:
    - Check if the provider is 'github'; if not, raise a `NotImplementedError`.
    - Verify if the current user has access to the GitHub installation ID specified in the repository metadata; if not, log an error and raise an `HTTPException` with a 403 status code.
    - Fetch an access token for the GitHub app using the installation ID from the repository metadata.
    - Determine the commit SHA to use based on specific conditions related to the repository name and organization.
    - Generate an upload key for storing the repository as a zip file, using the organization's hashed ID and the repository name.
    - Call `download_and_upload_repo` to download the repository and upload it to the specified location, using the access token and upload key.
    - Check if the upload was successful; if so, return a `JSONResponse` with a 202 status code and the download URL, otherwise return a `JSONResponse` with a 500 status code indicating an upload failure.
- **Output**:
    - A `JSONResponse` indicating the success or failure of the repository upload, including a download URL if successful.


---
### connect_git_provider_repo 
The `connect_git_provider_repo` function connects a list of Git repositories to a specified application by grouping them by installation ID and spawning a background task to handle GitLab events for each group.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A `UUID` representing the ID of the application to which the repositories are being connected.
    - `repos`: A list of `GitRepository` objects representing the repositories to be connected.
- **Control Flow**:
    - The function begins by looking up the `handle_gitlab_events` function using the `modal.Function.lookup` method with specific parameters.
    - The list of repositories (`repos`) is sorted by their `installation_id`.
    - The sorted repositories are grouped by `installation_id` using the `groupby` function from the `itertools` module.
    - For each group of repositories (grouped by `installation_id`), the function retrieves the corresponding application installation using `git_provider_app_installation_by_id`.
    - It checks if the `git_provider_app_id` of the installation matches the `application_id` and if the `organization_id` matches that of the `current_user`. If not, it raises an `HTTPException` with a 404 status code.
    - If the checks pass, it spawns a background task using `handle_gitlab_events.spawn` to handle the GitLab events for the group of repositories.
    - Finally, it returns a `JSONResponse` with a status code of 202 and a message indicating that the connection is in progress.
- **Output**:
    - The function returns a `JSONResponse` with a status code of 202 and a message indicating that the connection process is underway.


---
### create_app 
The `create_app` function creates a new Git provider application using the provided session and input data.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `gp_app_input`: An instance of `CreateGitProviderAppRequest` containing the input data required to create a Git provider application.
- **Control Flow**:
    - The function directly calls `create_git_provider_app` with the provided `session`, `gp_app_input`, and a predefined `aws_config`.
    - The function returns the result of the `create_git_provider_app` call.
- **Output**:
    - The function returns an instance of `GitProviderApp`, representing the newly created Git provider application.


---
### delete_app_installation 
The `delete_app_installation` function removes a specific application installation and returns a success message.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A string representing the ID of the application to be deleted.
    - `installation_id`: A string representing the ID of the installation to be deleted.
- **Control Flow**:
    - Calls `handle_group_access_revoke` with the session, current user's organization ID, application ID, installation ID, and AWS configuration to revoke access for the specified installation.
    - Returns a `JSONResponse` with a status code of 200 and a message indicating the installation was deleted.
- **Output**:
    - A `JSONResponse` object with a status code of 200 and a message indicating the installation was deleted.


---
### delete_git_provider_app 
The `delete_git_provider_app` function deletes a specified Git provider application for the current user's organization and returns a success message.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A string representing the ID of the application to be deleted.
- **Control Flow**:
    - The function calls `handle_delete_git_provider_app` with the session, the current user's organization ID, the application ID, and a predefined AWS configuration to perform the deletion.
    - After the deletion is handled, the function returns a `JSONResponse` with a status code of 200 (OK) and a message indicating that the app was deleted.
- **Output**:
    - A `JSONResponse` object with a status code of 200 and a message indicating successful deletion of the app.


---
### get_app_installation 
The `get_app_installation` function retrieves a list of Git provider app installations for a specific application and organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user, which includes the user's organization ID.
    - `application_id`: A string representing the unique identifier of the application for which installations are being retrieved.
- **Control Flow**:
    - The function calls `git_provider_app_installation_by_org_id` with the provided `session`, `current_user.organization_id`, and `application_id` to retrieve the installations.
    - The result of the call is stored in the `installs` variable.
    - The function returns the `installs` variable.
- **Output**:
    - A list of `GitProviderAppInstallation` objects representing the installations of the specified application for the user's organization.


---
### get_app_installation_webhook_info 
The function `get_app_installation_webhook_info` retrieves webhook configuration details for a specific app installation, ensuring the installation is valid and fetching necessary secrets.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A `UUID` representing the unique identifier of the application.
    - `installation_id`: A `UUID` representing the unique identifier of the installation.
- **Control Flow**:
    - Retrieve the app installation details using `git_provider_app_installation_by_id` with the provided session and installation_id.
    - Check if the `git_provider_app_id` of the retrieved installation matches the provided `application_id`.
    - If the IDs do not match, raise an `HTTPException` with a 404 status code indicating the installation was not found.
    - Read the secret associated with the installation using `AWSSecretManagementStrategy` and `format_secret_name`.
    - Create a `WebhookInfo` object with the callback URL, custom headers, secret token, SSL verification flag, and triggers.
    - Return the `WebhookInfo` object.
- **Output**:
    - Returns a `WebhookInfo` object containing the webhook configuration details for the specified app installation.


---
### get_apps 
The `get_apps` function retrieves a list of Git provider applications associated with the current user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user, which includes the user's organization ID.
- **Control Flow**:
    - The function calls `fetch_git_provider_apps_by_org_id` with the current session and the organization ID of the current user.
    - It directly returns the result of the `fetch_git_provider_apps_by_org_id` function call.
- **Output**:
    - A list of `GitProviderApp` objects associated with the current user's organization.


---
### get_codebase_asset 
The `get_codebase_asset` function retrieves a `PrimaryAsset` object from the database based on the organization ID and repository name, specifically for assets of kind 'CODEBASE'.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `org_id`: A string representing the organization ID to filter the `PrimaryAsset` records.
    - `repo_name`: A string representing the repository name to filter the `PrimaryAsset` records.
- **Control Flow**:
    - The function executes a SQL query using the `session` object to select a `PrimaryAsset` from the database.
    - The query filters `PrimaryAsset` records where `organization_id` matches `org_id`, `display_name` matches `repo_name`, and `kind` is `PrimaryAssetKind.CODEBASE`.
    - The query returns a single `PrimaryAsset` object or `None` if no matching record is found.
- **Output**:
    - The function returns a `PrimaryAsset` object if a matching record is found, otherwise it returns `None`.


---
### get_provider_authorize_url 
The `get_provider_authorize_url` function generates an authorization URL for a Git provider application and returns it in a JSON response.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user, containing user and organization identifiers.
    - `application_id`: A string representing the unique identifier of the application for which the authorization URL is being requested.
- **Control Flow**:
    - The function calls `authorize_git_provider` with the session, organization ID, user ID, application ID, and AWS configuration to generate an authorization URL.
    - The generated authorization URL is stored in the variable `auth_url`.
    - A `JSONResponse` is created with a status code of 200 (OK) and a content dictionary containing the `authorize_url` key with the value of `auth_url`.
    - The `JSONResponse` is returned as the output of the function.
- **Output**:
    - A `JSONResponse` object containing the authorization URL for the specified Git provider application.


---
### get_repositories_by_installation_id 
The function retrieves a list of Git repositories associated with a specific installation ID for a given application.
- **Inputs**:
    - `session`: An instance of CurrentSession, representing the current database session.
    - `current_user`: An instance of UserToken, representing the current authenticated user, including their organization and user IDs.
    - `application_id`: A string representing the ID of the application for which repositories are being fetched.
    - `installation_id`: A string representing the ID of the installation for which repositories are being fetched.
- **Control Flow**:
    - The function attempts to call fetch_group_repositories_by_installation_id with the provided session, current user's organization and user IDs, application ID, installation ID, and AWS configuration.
    - If the call is successful, it returns the list of GitRepository objects fetched.
    - If a GitProviderAccessTokenError is raised during the call, it logs an error message and raises an HTTPException with a 500 status code and 'Invalid Token' detail.
- **Output**:
    - A list of GitRepository objects associated with the specified installation ID.


---
### git_provider_app_callback 
The `git_provider_app_callback` function handles the callback from a Git provider's authorization process, processing the authorization code or error, and returns an HTML response to close the browser window.
- **Inputs**:
    - `session`: An instance of `CurrentSession`, representing the current database session.
    - `state`: A string representing the state parameter used to maintain state between the request and callback.
    - `code`: An optional string representing the authorization code returned by the Git provider.
    - `error`: An optional string representing any error message returned by the Git provider, defaulting to `None`.
- **Control Flow**:
    - Check if both `error` and `code` are not provided, and raise an HTTP 400 error if true.
    - Log the error if `error` is provided, indicating the user denied the authorization request.
    - If `code` is provided, call `handle_authorization_callback` with the session, code, state, and AWS configuration to process the authorization.
    - Prepare an HTML content string to close the browser window.
    - Return a `Response` object with the HTML content and media type set to `text/html`.
- **Output**:
    - A `Response` object containing HTML content to close the browser window, with a media type of `text/html`.


---
### github_callback 
The `github_callback` function handles the callback from GitHub's OAuth process, exchanges the authorization code for a token, and manages GitHub app installations in the database.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `code`: A string representing the authorization code received from GitHub.
    - `state`: A string representing the state parameter, which is base64 encoded and contains JSON data.
    - `installation_id`: A string representing the GitHub app installation ID.
    - `request`: An instance of `Request` representing the incoming HTTP request.
    - `response`: An instance of `Response` representing the outgoing HTTP response.
- **Control Flow**:
    - Check if the `code` is not provided, raise an HTTP 400 error if missing.
    - Decode the `state` parameter from base64 and parse it as JSON to extract `org_id` and `user_id`.
    - Format a secret key using `org_id`, `user_id`, and a fixed string 'github'.
    - Exchange the `code` for a token using `exchange_code_for_token` and serialize the token data to JSON.
    - Write the token data to a secret store using the formatted secret key.
    - Query the database to check if a GitHub app installation already exists for the given `org_id` and `installation_id`.
    - If no existing installation is found, create a new `GithubAppInstallation` record, add it to the session, and commit the transaction.
    - Look up a function `connect_repos_for_installation` using `modal.Function.lookup` and spawn it with the `installation_id`.
    - Return an HTML response that closes the window.
- **Output**:
    - An `OkResponse` object indicating the operation was successful, with an HTML response that closes the window.


---
### gitlab_webhook 
The `gitlab_webhook` function processes incoming GitLab webhook events, verifies their authenticity, and handles push events accordingly.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `body_data`: A dictionary containing the JSON body and headers of the incoming request, extracted using the `_extract_body_and_headers` dependency.
- **Control Flow**:
    - Extract the JSON body and headers from `body_data`.
    - Retrieve the `object_kind` from the body to determine the type of event.
    - Extract the `installation_id` and `incoming_secret_token` from the headers.
    - Read the secret token associated with the `installation_id` using AWS Secret Management.
    - If the secret token is not found, log an error and raise an HTTP 403 exception for insufficient permissions.
    - Compare the `secret_token` with the `incoming_secret_token`; if they do not match, log an error and raise an HTTP 403 exception.
    - Retrieve the app installation details using the `installation_id`.
    - If the event is a 'push' event, call `handle_gitlab_push_event` to process it.
    - Return a JSON response with status 202 and a message indicating the event was ignored if not a push event.
- **Output**:
    - A `JSONResponse` with status code 202 and a message indicating the event was ignored, unless a push event is handled.


---
### handle_gitlab_push_event 
The `handle_gitlab_push_event` function processes GitLab push events, verifying the branch and triggering further event handling if conditions are met.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `app_id`: A `UUID` representing the application ID associated with the GitLab event.
    - `installation_id`: A string representing the installation ID of the GitLab app.
    - `body`: A dictionary containing the payload of the GitLab push event, including repository and project details.
- **Control Flow**:
    - Extracts repository and project details from the `body` dictionary, including repository name, project ID, full name, default branch, pushed reference, and commit hash.
    - Retrieves the app installation details using the `installation_id` and checks the organization ID.
    - Checks if the pushed reference matches the default branch; if not, logs an informational message and returns a JSON response indicating the event is ignored.
    - Logs a message if the push event is on the default branch.
    - Verifies if the app installation's Git provider app ID matches the provided `app_id`; raises an HTTP 404 exception if not.
    - Prepares a list of pushed repositories with relevant details.
    - Looks up the `handle_gitlab_events` function using the `modal.Function.lookup` method and spawns it with the installation ID, organization ID, and the list of pushed repositories.
    - Returns a JSON response with a status code of 202 indicating the event was accepted.
- **Output**:
    - A `JSONResponse` object with a status code of 202, indicating the event was accepted, and a message indicating the result of the push event handling.


---
### handle_installation_delete_event 
The function `handle_installation_delete_event` processes a GitHub app installation deletion event by removing the installation record from the database and triggering a background job to handle the disconnection of associated repositories.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `body`: A dictionary containing the event data, including the installation ID and a list of repositories associated with the installation.
- **Control Flow**:
    - Extract the installation ID from the event body and convert it to a string.
    - Query the database to find the installation record using the installation ID.
    - Retrieve the organization ID from the installation record.
    - Delete the installation record from the database and commit the transaction.
    - Set the installation ID to `None` to indicate its deletion.
    - Iterate over the list of repositories in the event body and append each repository's details to the `repos_deleted` list.
    - Look up the `handle_github_events` function using the `modal.Function.lookup` method.
    - Spawn a background job using `handle_github_events.spawn` with the installation ID, organization ID, and lists of added, deleted, and pushed repositories.
    - Log an informational message indicating the processing of the installation delete event.
    - Return a `JSONResponse` with a status code of 202 (Accepted) and an empty message.
- **Output**:
    - A `JSONResponse` with a status code of 202 (Accepted) and an empty message, indicating that the event was processed successfully.


---
### handle_installation_modified_event 
The `handle_installation_modified_event` function processes GitHub installation modification events by updating the list of added and removed repositories and triggering a background job to handle these changes.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `body`: A dictionary containing the event data, including installation ID and lists of added and removed repositories.
- **Control Flow**:
    - Extract the installation ID from the event body and convert it to a string.
    - Retrieve the GitHub app installation record from the database using the installation ID.
    - If the installation record is not found, log a warning and return an HTTP 202 response with an empty message.
    - Extract the lists of added and removed repositories from the event body.
    - Initialize empty lists for added, deleted, and pushed repositories.
    - Iterate over the added repositories and append their details to the `repos_added` list.
    - Iterate over the removed repositories and append their details to the `repos_deleted` list.
    - Look up the `handle_github_events` function using the `modal.Function.lookup` method.
    - Spawn a background job using `handle_github_events.spawn` with the installation ID, organization ID, and lists of added, deleted, and pushed repositories.
    - Log an informational message indicating the processing of the installation modified event.
    - Return an HTTP 202 response with an empty message.
- **Output**:
    - A `JSONResponse` with a status code of 202 (Accepted) and an empty message, indicating that the event has been processed.


---
### handle_ping_event 
The `handle_ping_event` function logs a ping event from GitHub and returns a JSON response indicating the event was received.
- **Inputs**:
    - None
- **Control Flow**:
    - Logs the receipt of a ping event from GitHub using the logger.
    - Returns a JSON response with a status code of 202 (Accepted) and a message indicating the ping was received.
- **Output**:
    - A `JSONResponse` object with a status code of 202 and a message indicating the ping was received.


---
### handle_push_event 
The `handle_push_event` function processes GitHub push events, filtering them based on specific branch criteria and triggering background processing for valid events.
- **Inputs**:
    - `session`: An instance of `CurrentSession`, representing the current database session for querying and updating records.
    - `body`: A dictionary containing the payload of the GitHub push event, including repository details, branch information, and commit data.
- **Control Flow**:
    - Extracts repository details such as organization name, repository name, repository ID, default branch, pushed reference, installation ID, and commit hash from the `body` dictionary.
    - Checks if the organization and repository match specific criteria (e.g., 'no-OS' or 'diff-tests') and if the pushed reference matches the expected branch for these repositories.
    - If the event does not match the criteria, logs an informational message and returns a JSON response indicating the event is ignored.
    - If the event matches the criteria, logs a message indicating a push event on the default branch and proceeds to process the event.
    - Queries the database for the GitHub app installation using the installation ID and checks if it exists.
    - If the installation is not found, logs a warning and returns a JSON response indicating the need for a database entry.
    - Queries for the primary codebase asset associated with the organization and repository name.
    - If the codebase asset is not found, logs a warning and returns a JSON response indicating the absence of the asset.
    - Prepares lists for repositories added, deleted, and pushed, and includes the current repository in the pushed list.
    - Looks up and spawns a background job to handle GitHub events using the `modal.Function.lookup` method.
    - Logs a message indicating the push event is being processed in a background job.
    - Returns a JSON response with a status code of 202, indicating the event is being processed.
- **Output**:
    - A `JSONResponse` object with a status code of 202, indicating whether the push event was ignored or is being processed.


---
### update_git_provider_group_access_token 
The function `update_git_provider_group_access_token` updates a group access token for a specific Git provider application installation and returns a success or error response.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `current_user`: An instance of `UserToken` representing the current authenticated user.
    - `application_id`: A string representing the ID of the Git provider application.
    - `installation_id`: A string representing the ID of the installation for which the token is being updated.
    - `new_gat`: An instance of `GroupAccessToken` representing the new group access token to be updated.
- **Control Flow**:
    - The function attempts to update the group access token by calling `update_group_access_token` with the provided session, organization ID, application ID, installation ID, new group access token, and AWS configuration.
    - If the update is successful, it returns a `JSONResponse` with a status code of 200 and a message indicating the token was updated.
    - If a `GitProviderAccessTokenError` is raised during the update, it logs the exception and raises an `HTTPException` with a status code of 500 and a detail message indicating an invalid token.
- **Output**:
    - A `JSONResponse` object indicating the success or failure of the token update operation, with a status code and message.


---
### verify_github_signature 
The `verify_github_signature` function checks the validity of a GitHub webhook signature using a secret token and raises an exception if the verification fails.
- **Inputs**:
    - `body_bytes`: The raw bytes of the request body that need to be verified.
    - `secret_token`: The secret token used to generate the expected signature, typically the GitHub webhook secret.
    - `signature_header`: The signature header received from GitHub, which contains the signature to be verified.
- **Control Flow**:
    - The function attempts to verify the signature by calling the `verify_signature` function with the provided inputs.
    - If the signature verification fails, an `HTTPException` is caught, a warning is logged, and the exception is re-raised.
- **Output**:
    - The function does not return any value; it raises an exception if the signature verification fails.


---
### verify_signature 
The `verify_signature` function validates that a payload was sent from GitHub by checking the SHA256 signature against a provided secret token.
- **Inputs**:
    - `payload_body`: The original request body to verify, typically obtained from `request.body()`.
    - `secret_token`: The GitHub app webhook token used for generating the expected signature.
    - `signature_header`: The signature header received from GitHub, specifically the `x-hub-signature-256` header.
- **Control Flow**:
    - Check if the `signature_header` is missing; if so, raise an HTTP 403 exception with a specific error message.
    - Create a new HMAC object using the `secret_token` and `payload_body`, with SHA256 as the digest mode.
    - Generate the expected signature by prefixing the HMAC digest with 'sha256='.
    - Compare the expected signature with the `signature_header` using `hmac.compare_digest` for a secure comparison.
    - If the signatures do not match, raise an HTTP 403 exception with a specific error message.
- **Output**:
    - The function does not return any value; it raises an HTTPException with a 403 status code if the signature verification fails.


---
### webhook 
The `webhook` function processes GitHub webhook events by verifying the signature and handling different event types such as push, ping, installation, and installation_repositories.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `body_data`: A dictionary containing the raw body, JSON body, and headers of the incoming request, extracted using the `_extract_body_and_headers` dependency.
- **Control Flow**:
    - Extracts the raw body, JSON body, and headers from `body_data`.
    - Retrieves the GitHub event type from the headers using the key `x-github-event`.
    - Retrieves the signature header from the headers using the key `x-hub-signature-256`.
    - Fetches the secret token from the application settings.
    - Calls `verify_github_signature` to ensure the request is from GitHub by verifying the signature.
    - Checks the type of GitHub event and calls the corresponding handler function: `handle_push_event` for 'push', `handle_ping_event` for 'ping', `handle_installation_delete_event` for 'installation' with 'deleted' action, and `handle_installation_modified_event` for 'installation_repositories'.
    - Logs an info message and returns a JSON response with a message 'Event ignored' if the event type is unhandled.
- **Output**:
    - A `JSONResponse` object indicating the result of processing the webhook event, with different status codes and messages based on the event type and processing outcome.


