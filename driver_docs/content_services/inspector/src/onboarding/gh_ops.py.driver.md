# Purpose
This Python script is designed to interact with GitHub's API to manage repositories, primarily focusing on authentication, data retrieval, and repository management tasks. It provides a set of functions that facilitate the generation of JSON Web Tokens (JWT) for authentication, fetching access tokens for GitHub app installations, retrieving repository information such as default branches and commits, and downloading repository content as ZIP files. Additionally, it includes functionality to upload repository data to an S3 bucket with metadata, create pull requests for documentation updates, and manage versioning and asset tracking within a database using SQLAlchemy.

The script is structured as a library file, intended to be imported and used within a larger application or system. It leverages several external libraries, such as `httpx` for HTTP requests, `jwt` for token encoding, and `sqlalchemy` for database interactions. The code defines a public API for interacting with GitHub repositories, including functions for generating JWTs, fetching access tokens, downloading repository content, and creating pull requests. It also integrates with a database to manage versioning and asset metadata, ensuring that repository changes are tracked and documented efficiently. The script is designed to be robust, with error handling for HTTP status errors and database integrity issues, making it suitable for use in production environments where reliable GitHub integration is required.
# Imports and Dependencies

---
- `base64`
- `hashlib`
- `logging`
- `os`
- `time`
- `datetime.UTC`
- `datetime.datetime`
- `uuid.UUID`
- `httpx`
- `jwt`
- `modal`
- `requests`
- `onboarding.onboard_utils.AccessTokenError`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.Session`
- `sqlmodel.select`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.db.engine`
- `database.models_v1.InspectorRun`
- `database.models_v1.UsageEvent`
- `database.models_v1.UsageEventType`
- `database.models_v1.UsageSession`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.models_v2_enums.VersionStatus`
- `onboarding.onboard_utils.upload_to_s3_with_metadata`
- `sqlalchemy.exc.IntegrityError`


# Global Variables

---
### logger
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module. It is configured to use the default logger with the name of the current module, which is typically the name of the file where the logger is created. This logger is used to record log messages throughout the application, providing a way to track events and debug information.
- **Use**: The `logger` is used to log informational messages about the status and data retrieved from the GitHub API, as well as other significant events in the application.


# Functions

---
### create_pull_request
The `create_pull_request` function creates a pull request on GitHub for documentation changes in a specified branch of a repository.
- **Inputs**:
    - `full_name`: The full name of the GitHub repository in the format 'owner/repo'.
    - `branch`: The name of the branch for which the pull request is to be created.
    - `access_token`: A GitHub access token used for authentication.
    - `commit_slug`: A string representing the commit identifier for which the documentation update is being made.
- **Control Flow**:
    - Set up HTTP headers for GitHub API authentication using the provided access token.
    - Use an HTTP client to check for existing open pull requests for the specified branch in the repository.
    - Fetch the default branch name of the repository using the `fetch_github_default_branch_name` function.
    - If no existing pull request is found, prepare the data for a new pull request, including the title and body with a logo image.
    - Attempt to create a new pull request by sending a POST request to the GitHub API with the prepared data.
    - If the pull request creation is successful, print the URL of the created pull request.
    - Handle HTTP errors, specifically checking for a 422 status code to indicate that no changes exist to create a pull request for, and print a warning message if so.
- **Output**:
    - The function does not return any value; it prints the URL of the created pull request or a warning message if no changes exist to create a pull request.


---
### download_and_upload_repo
The function `download_and_upload_repo` manages the process of downloading a GitHub repository, handling versioning and asset management, and uploading the repository to S3 with metadata.
- **Inputs**:
    - `org_id`: A string representing the organization ID.
    - `repo`: A dictionary containing repository details, including 'id', 'name', 'full_name', and optionally 'commit'.
    - `access_token`: A string representing the GitHub access token for authentication.
    - `install_id`: A string representing the installation ID for the GitHub app.
    - `is_push`: A boolean flag indicating whether the operation is triggered by a push event (default is False).
- **Control Flow**:
    - Check if the 'commit' key exists in the 'repo' dictionary; if not, fetch the default branch and commit using the repository's full name and access token.
    - Open a database session and begin a transaction to handle asset and version management.
    - If 'is_push' is True, attempt to find the primary asset in the database using the organization ID and repository ID.
    - If the primary asset is found, check the status of its versions to determine the appropriate action (e.g., create a new version, delete and restart an inspection, or skip processing).
    - If 'is_push' is False, create a new primary asset and version in the database for the repository.
    - Handle any IntegrityError exceptions that occur during database operations by printing an error message and returning the repository dictionary.
    - Generate metadata for the codebase using the provided and derived information.
    - Download the repository as a zip file from GitHub using the full name, commit, and access token.
    - Construct an upload key using the organization ID, primary asset ID, version ID, and repository name.
    - Upload the downloaded zip file to S3 with the generated metadata and constructed upload key.
    - Return None after successful upload.
- **Output**:
    - The function returns None if the process completes successfully, or the input 'repo' dictionary if an error occurs during processing.


---
### download_github_repo_zip
The `download_github_repo_zip` function downloads a GitHub repository as a zip file for a specific commit using an access token for authentication.
- **Inputs**:
    - `full_name`: The full name of the GitHub repository in the format 'owner/repo'.
    - `commit`: The specific commit SHA for which the repository zip file is to be downloaded.
    - `access_token`: A GitHub access token used for authentication to access the repository.
- **Control Flow**:
    - Set the authorization header using the provided access token.
    - Construct the URL for the zip file of the specified repository and commit.
    - Make a GET request to the constructed URL with the authorization header, a timeout of 120 seconds, and allow redirects.
    - Raise an HTTP error if the request fails.
    - Return the content of the response, which is the zip file in bytes.
- **Output**:
    - The function returns the content of the zip file as bytes.


---
### fetch_app_access_token
The `fetch_app_access_token` function retrieves an access token for a GitHub application installation using a JWT for authentication.
- **Inputs**:
    - `installation_id`: A string representing the unique identifier of the GitHub application installation for which the access token is being requested.
- **Control Flow**:
    - Constructs the URL for the GitHub API endpoint to fetch access tokens for the specified installation ID.
    - Generates a JSON Web Token (JWT) using the `generate_jwt` function for authentication.
    - Creates an HTTP client using `httpx.Client` to send a POST request to the constructed URL with the JWT in the Authorization header.
    - Checks the response status; if the status code is 404, raises an `AccessTokenError` indicating the installation was not found.
    - Parses the JSON response to extract the token data.
    - Checks if the 'token' key is present in the response; if not, raises an `AccessTokenError` indicating the token was not found.
    - Returns the access token from the response.
- **Output**:
    - A string representing the access token for the specified GitHub application installation.


---
### fetch_default_branch_and_commit
The function fetches the default branch and the latest commit SHA of a GitHub repository using the GitHub API.
- **Inputs**:
    - `full_repo_name`: A string representing the full name of the GitHub repository in the format 'owner/repo'.
    - `access_token`: A string representing the GitHub access token used for authentication in API requests.
- **Control Flow**:
    - Set up the authorization headers using the provided access token.
    - Construct the GitHub repository URL using the full repository name.
    - Make a GET request to the GitHub API to retrieve repository data.
    - Parse the JSON response to extract the default branch name.
    - Construct the URL for the default branch using the repository URL and the default branch name.
    - Make another GET request to the GitHub API to retrieve data for the default branch.
    - Parse the JSON response to extract the SHA of the latest commit on the default branch.
    - Log information about the retrieved repository and branch data.
    - Return the SHA of the latest commit on the default branch.
- **Output**:
    - A string representing the SHA of the latest commit on the default branch of the specified GitHub repository.


---
### fetch_github_default_branch_name
The function fetches the default branch name of a specified GitHub repository using the GitHub API.
- **Inputs**:
    - `full_repo_name`: A string representing the full name of the GitHub repository, typically in the format 'owner/repo'.
    - `access_token`: A string representing the GitHub access token used for authentication to access the GitHub API.
- **Control Flow**:
    - Set up the authorization headers using the provided access token.
    - Construct the GitHub repository URL using the full repository name.
    - Make a GET request to the GitHub API to retrieve repository information.
    - Parse the JSON response to extract the default branch name.
    - Return the default branch name.
- **Output**:
    - A string representing the default branch name of the specified GitHub repository.


---
### generate_codebase_metadata
The `generate_codebase_metadata` function creates a dictionary containing metadata for a codebase, including organization, repository, and version details.
- **Inputs**:
    - `org_id`: A string representing the organization ID.
    - `full_repo_name`: A string representing the full name of the repository, used for debugging purposes.
    - `repo_id`: A string or integer representing the repository ID, used for debugging purposes.
    - `provider`: A string representing the provider of the codebase, such as 'github'.
    - `version_id`: A string or UUID representing the version ID of the codebase.
    - `asset_name`: A string representing the name of the asset.
    - `install_id`: A string representing the installation ID.
- **Control Flow**:
    - The function imports `PrimaryAssetKind` from `database.models_v2_enums` to use as a constant value for `asset_kind`.
    - It constructs a dictionary with keys corresponding to various metadata fields such as `unhashed_organization_id`, `full_repo_name`, `provider`, `version_id`, `repository_id`, `asset_name`, `asset_kind`, and `install_id`.
    - The `version_id` and `repository_id` are converted to strings to ensure consistent data types in the dictionary.
- **Output**:
    - The function returns a dictionary containing metadata about the codebase, including organization ID, repository name and ID, provider, version ID, asset name, asset kind, and installation ID.


---
### generate_jwt
The `generate_jwt` function creates a JSON Web Token (JWT) using environment variables for authentication with GitHub.
- **Inputs**:
    - None
- **Control Flow**:
    - The function initializes a `payload` dictionary with three keys: `iat` (issued at time), `exp` (expiration time set to 10 minutes from now), and `iss` (issuer, set to the GitHub client ID from environment variables).
    - It decodes a base64-encoded PEM secret from an environment variable to obtain the private key.
    - The function then encodes the payload into a JWT using the decoded PEM and the RS256 algorithm, and returns the encoded JWT.
- **Output**:
    - The function returns a JWT as a string.


---
### get_github_repo_url
The function `get_github_repo_url` constructs a GitHub API URL for a given repository name.
- **Inputs**:
    - `full_repo_name`: A string representing the full name of the GitHub repository, typically in the format 'owner/repo'.
- **Control Flow**:
    - The function takes a single input parameter, `full_repo_name`.
    - It constructs a URL string by embedding the `full_repo_name` into a GitHub API URL template.
    - The constructed URL is returned as the output.
- **Output**:
    - A string representing the GitHub API URL for accessing the specified repository's information.


---
### get_repo_clone_info_from_id
The function retrieves the clone URL and full name of a GitHub repository using its repository ID and a GitHub token.
- **Inputs**:
    - `repo_id`: A string representing the unique identifier of the GitHub repository.
    - `github_token`: A string representing the GitHub token used for authentication.
- **Control Flow**:
    - Set up headers for the HTTP request using the provided GitHub token for authorization.
    - Create an HTTP client using httpx and send a GET request to the GitHub API to fetch repository details using the provided repo_id.
    - Raise an exception if the HTTP request fails (non-2xx status code).
    - Parse the JSON response to extract the repository's full name.
    - Construct the clone URL using the full name and the GitHub token.
    - Return the clone URL and the full name as a tuple.
- **Output**:
    - A tuple containing the clone URL and the full name of the repository.


