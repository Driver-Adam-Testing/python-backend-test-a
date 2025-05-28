# Purpose
This Python script is designed to interact with GitLab repositories, providing functionality for managing repository access, downloading repositories, generating metadata, and handling version control. It includes functions to fetch access tokens from AWS Secrets Manager, download repository archives, generate metadata for codebases, and upload these archives to AWS S3 with associated metadata. The script also supports creating pull requests and fetching repository information such as the default branch name and clone URLs. The code is structured to handle both push events and initial repository connections, managing different version statuses and ensuring that the most up-to-date state is reflected in the documentation generated.

The script is a collection of functions that integrate with external services like AWS and GitLab, making it suitable for use in a larger application or system that requires automated repository management and version control. It leverages SQLAlchemy for database interactions, particularly for managing version and asset records, and uses the `requests` library for HTTP requests to GitLab's API. The script is not a standalone executable but rather a module intended to be part of a larger system, possibly invoked by other components or services that handle repository management tasks. The presence of TODO comments indicates areas for future enhancement, suggesting that the script is part of an evolving codebase.
# Imports and Dependencies

---
- `hashlib`
- `os`
- `datetime.UTC`
- `datetime.datetime`
- `uuid.UUID`
- `modal`
- `requests`
- `onboarding.onboard_utils.AccessTokenError`
- `onboarding.onboard_utils.upload_to_s3_with_metadata`
- `shared.interfaces.aws_client_config.AWSClientConfig`
- `shared.secret_management.aws_secret_management.AWSSecretManagementStrategy`
- `shared.secret_management.aws_secret_management.format_secret_name`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.Session`
- `sqlmodel.select`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.db.engine`
- `database.models_v1.GitProviderAppInstallation`
- `database.models_v1.InspectorRun`
- `database.models_v1.UsageEvent`
- `database.models_v1.UsageEventType`
- `database.models_v1.UsageSession`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `database.models_v2_enums.PrimaryAssetKind`
- `database.models_v2_enums.VersionStatus`
- `sqlalchemy.exc.IntegrityError`


# Functions

---
### create_pull_request
The `create_pull_request` function creates a pull request on a GitLab repository from a specified branch to the default branch.
- **Inputs**:
    - `base_url`: The base URL of the GitLab instance where the repository is hosted.
    - `repo_id`: The unique identifier of the repository on GitLab.
    - `access_token`: The access token used for authentication with the GitLab API.
    - `branch`: The name of the source branch from which the pull request will be created.
    - `commit_slug`: A string representing the commit identifier used in the pull request title.
- **Control Flow**:
    - Fetch the default branch name of the repository using the `fetch_gitlab_default_branch_name` function.
    - Set up the authorization headers using the provided access token.
    - Send a POST request to the GitLab API to create a merge request from the specified branch to the default branch.
    - Raise an exception if the request fails.
    - Print the URL of the created pull request if successful.
- **Output**:
    - The function does not return any value; it prints the URL of the created pull request upon success.


---
### download_and_upload_repo
The function `download_and_upload_repo` manages the download of a repository from a Git provider and uploads it to an S3 bucket, handling versioning and asset management in the process.
- **Inputs**:
    - `org_id`: A string representing the organization ID.
    - `repo`: A dictionary containing metadata about the repository, including its ID, name, latest commit, and installation ID.
    - `access_token`: A string representing the access token for authentication with the Git provider.
    - `is_push`: A boolean flag indicating whether the operation is triggered by a push event (default is False).
- **Control Flow**:
    - Imports necessary modules and classes for database interaction and error handling.
    - Extracts repository details such as ID, name, commit ID, and installation ID from the `repo` dictionary.
    - Opens a database session and retrieves the Git provider application installation details using the installation ID.
    - Checks if the operation is a push event (`is_push` is True) and handles versioning logic based on the status of existing versions of the primary asset.
    - If the primary asset does not exist for a push event, logs an error and returns the repository data.
    - Handles different version statuses (CONNECTED, GENERATING, GENERATION_COMPLETE, GENERATION_ERROR) to manage version creation, deletion, and inspection restarts.
    - If not a push event, creates a new primary asset and version in the database.
    - Handles `IntegrityError` exceptions by logging a failure message and returning the repository data.
    - Generates metadata for the codebase using the `generate_codebase_metadata` function.
    - Downloads the repository as a zip file using the `download_repo` function.
    - Calculates a hashed organization ID and constructs an S3 upload key.
    - Uploads the downloaded repository to S3 with metadata using the `upload_to_s3_with_metadata` function.
    - Logs success messages for download and upload operations.
- **Output**:
    - Returns `None` if the operation is successful, or the `repo` dictionary if an error occurs during asset or version creation.


---
### download_repo
The `download_repo` function downloads a specific commit of a repository from a GitLab server as a zip archive.
- **Inputs**:
    - `base_url`: The base URL of the GitLab server from which the repository is to be downloaded.
    - `repo_id`: The unique identifier of the repository to be downloaded.
    - `commit`: The specific commit SHA of the repository to be downloaded.
    - `access_token`: The access token used for authentication to access the repository.
- **Control Flow**:
    - Set the authorization header using the provided access token.
    - Make a GET request to the GitLab API to download the repository archive as a zip file for the specified commit.
    - Raise an HTTP error if the request fails.
    - Return the content of the response, which is the zip file of the repository.
- **Output**:
    - The function returns the content of the response as bytes, which is the zip archive of the specified repository commit.


---
### fetch_access_token
The `fetch_access_token` function retrieves a group access token for a given installation ID from AWS Secrets Manager.
- **Inputs**:
    - `installation_id`: A string representing the installation ID for which the access token is to be fetched.
- **Control Flow**:
    - Prints a message indicating the start of the token fetching process for the given installation ID.
    - Formats the secret name using the installation ID to create a key for accessing the secret.
    - Initializes an AWSSecretManagementStrategy object with AWS client configuration using environment variables for region, access key ID, and secret access key.
    - Reads the secret value from AWS Secrets Manager using the formatted secret name as the key.
    - Checks if the secret value is not found, and raises an AccessTokenError if it is missing.
    - Extracts the 'token' from the secret value, which is the group access token.
    - Returns the group access token.
- **Output**:
    - A string representing the group access token associated with the given installation ID.


---
### fetch_gitlab_default_branch_name
The function fetches the default branch name of a GitLab repository using the GitLab API.
- **Inputs**:
    - `base_url`: The base URL of the GitLab instance, typically in the format 'https://gitlab.example.com'.
    - `repo_id`: The unique identifier of the GitLab repository for which the default branch name is to be fetched.
    - `access_token`: A personal access token with the necessary permissions to access the GitLab API and retrieve repository information.
- **Control Flow**:
    - Set up the authorization headers using the provided access token.
    - Make a GET request to the GitLab API endpoint for the specified repository using the base URL and repo ID.
    - Raise an exception if the HTTP request fails (non-2xx status code).
    - Parse the JSON response to extract and return the 'default_branch' field.
- **Output**:
    - The function returns a string representing the name of the default branch of the specified GitLab repository.


---
### generate_codebase_metadata
The `generate_codebase_metadata` function creates a dictionary containing metadata about a codebase repository.
- **Inputs**:
    - `org_id`: A string representing the organization ID.
    - `full_repo_name`: A string representing the full name of the repository, used for debugging purposes.
    - `repo_id`: A string or integer representing the repository ID, used for debugging purposes.
    - `provider`: A string representing the provider of the repository.
    - `version_id`: A string or UUID representing the version ID of the repository.
    - `asset_name`: A string representing the name of the asset.
    - `install_id`: A string representing the installation ID.
- **Control Flow**:
    - Imports the `PrimaryAssetKind` from `database.models_v2_enums` to use as a constant value in the metadata.
    - Returns a dictionary with keys for organization ID, full repository name, provider, version ID, repository ID, asset name, asset kind, and installation ID.
    - Converts `version_id` and `repo_id` to strings before including them in the dictionary.
- **Output**:
    - A dictionary containing metadata about the codebase, including organization ID, full repository name, provider, version ID, repository ID, asset name, asset kind, and installation ID.


---
### get_gitlab_username
The function `get_gitlab_username` retrieves the GitLab username associated with a given access token from a specified GitLab instance.
- **Inputs**:
    - `base_url`: The base URL of the GitLab instance from which the username is to be fetched.
    - `access_token`: The access token used for authentication to access the GitLab API.
- **Control Flow**:
    - Constructs the API endpoint URL by appending '/api/v4/user' to the provided base URL, ensuring no trailing slashes.
    - Sets up the request headers with the provided access token under the 'PRIVATE-TOKEN' key.
    - Prints a message indicating the URL from which the username is being fetched.
    - Sends a GET request to the constructed URL with the specified headers.
    - Raises an HTTP error if the request fails (non-2xx status code).
    - Prints the JSON response from the API call.
    - Extracts and returns the 'username' field from the JSON response.
- **Output**:
    - Returns the GitLab username as a string.


---
### get_repo_clone_info_from_id
The function retrieves the clone URL and full name of a GitLab repository using its ID and an access token.
- **Inputs**:
    - `base_url`: The base URL of the GitLab instance, used to construct the API endpoint.
    - `repo_id`: The unique identifier of the repository whose clone information is to be retrieved.
    - `access_token`: The access token for authenticating the API request to GitLab.
- **Control Flow**:
    - Set up the authorization headers using the provided access token.
    - Make a GET request to the GitLab API to retrieve repository details using the base URL and repo ID.
    - Raise an exception if the request fails.
    - Extract the clone URL and full name of the repository from the JSON response.
    - Retrieve the GitLab username using the base URL and access token.
    - If both the clone URL and username are available, modify the clone URL to include the username and access token for authentication.
    - Raise a ValueError if either the clone URL or username is missing.
    - Return the modified clone URL and the full name of the repository.
- **Output**:
    - A tuple containing the modified clone URL and the full name of the repository.


