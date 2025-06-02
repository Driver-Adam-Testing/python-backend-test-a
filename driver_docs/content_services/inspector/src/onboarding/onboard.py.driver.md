# Purpose
This Python code file is designed to handle the integration and management of repositories from GitHub and GitLab within a larger application ecosystem. It provides a set of functions that are decorated with `@app.function`, indicating that they are intended to be executed as serverless functions using the Modal framework. The primary purpose of these functions is to manage events related to repository additions, deletions, and updates, as well as to facilitate the connection and processing of codebases. The file includes functions for handling GitHub and GitLab events, connecting repositories for specific installations, and running codebase connections. These functions utilize various external libraries and services, such as SQLAlchemy for database interactions, requests for HTTP requests, and AWS S3 for file storage.

The code is structured to handle asynchronous operations using `ThreadPoolExecutor` and manages secrets and proxies for secure and efficient communication with external services. It also includes logic for downloading repositories, processing them, and updating the database with relevant metadata. The file is part of a larger system that likely involves multiple components working together to provide comprehensive repository management and codebase analysis. The use of Modal's serverless functions suggests that this code is designed to be scalable and efficient, handling potentially large volumes of repository data across different environments.
# Imports and Dependencies

---
- `hashlib`
- `os`
- `re`
- `concurrent.futures.ThreadPoolExecutor`
- `concurrent.futures.wait`
- `pathlib.Path`
- `uuid.uuid4`
- `modal`
- `common.app`
- `database.models_v2_enums.ContentKind`
- `database.models_v2_enums.NodeKind`
- `database.models_v2_enums.VersionStatus`
- `database.db.engine`
- `database.models_v1.GithubAppInstallation`
- `database.models_v2.PrimaryAsset`
- `onboarding.gh_ops.download_and_upload_repo`
- `onboarding.gh_ops.fetch_app_access_token`
- `onboarding.onboard_utils.AccessTokenError`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.Session`
- `sqlmodel.select`
- `onboarding.gitlab_ops`
- `requests`
- `database.models_v1.DerivedContent`
- `database.models_v1.GitProviderKind`
- `database.models_v2.Node`
- `database.models_v2.Version`
- `onboarding.onboard_utils.create_bucket_if_dne`
- `onboarding.onboard_utils.download_file_from_presigned_url`
- `onboarding.onboard_utils.is_driverignored`
- `onboarding.onboard_utils.is_on_blacklist`
- `onboarding.onboard_utils.load_driverignore`
- `onboarding.onboard_utils.parse_presigned_url`
- `onboarding.onboard_utils.run_file_stats_and_reencode`
- `onboarding.onboard_utils.unpack_archive_to_finalized_path`
- `shared.usage.utils.bytes_to_sloc`
- `sqlalchemy.exc.IntegrityError`
- `sqlmodel.update`
- `boto3.client`
- `boto3.resource`


# Global Variables

---
### image 
- **Type**: `modal.Image`
- **Description**: The `image` variable is an instance of `modal.Image` configured with a Debian Slim base image and Python 3.12. It includes several local directories and files added to the image, installs packages via `apt` and `pip`, and uses `poetry` for dependency management from a `pyproject.toml` file.
- **Use**: This variable is used as the base image for various functions defined in the application, providing a consistent environment with necessary dependencies and files.


# Functions

---
### connect_repos_for_installation 
The function `connect_repos_for_installation` connects GitHub repositories to a specific installation by fetching repository data and spawning a process to handle GitHub events.
- **Inputs**:
    - `github_installation_id`: A string representing the GitHub installation ID for which repositories need to be connected.
- **Control Flow**:
    - The function starts by establishing a session with the database to retrieve the installation details using the provided GitHub installation ID.
    - It attempts to fetch an access token for the GitHub installation; if unsuccessful, it raises an AccessTokenError.
    - With the access token, it makes a request to the GitHub API to retrieve the list of repositories associated with the installation.
    - The function processes the response to extract repository details and appends them to a list of added repositories.
    - It checks for pagination in the API response and continues fetching additional pages of repositories until no more pages are available or a maximum page limit is reached.
    - Finally, it spawns a process to handle GitHub events for the installation, passing the list of added repositories.
- **Output**:
    - The function does not return any value (returns None), but it prints status messages and spawns a process to handle GitHub events for the connected repositories.


---
### connect_unconnected_repos 
The function `connect_unconnected_repos` connects GitHub repositories that are not yet connected to a system by fetching their details and spawning a process to handle their events.
- **Inputs**:
    - None
- **Control Flow**:
    - The function starts by importing necessary modules and setting up a database session using `Session(engine)`.
    - It retrieves all GitHub app installations from the database using a SQL query and iterates over each installation.
    - For each installation, it attempts to fetch an access token using `fetch_app_access_token`. If an `AccessTokenError` is raised, it logs a message and continues to the next installation.
    - If a token is successfully retrieved, it makes a GET request to the GitHub API to fetch the list of repositories associated with the installation.
    - The function processes the response to extract repository details and appends them to a list `repos_added`.
    - It checks for pagination in the API response and continues fetching additional pages of repositories until no more pages are available or a maximum page limit is reached.
    - After collecting all repositories, it spawns a process using `handle_github_events.spawn` to handle the events for the installation and the collected repositories.
    - Finally, it logs the number of connected repositories and their details.
- **Output**:
    - The function does not return any value; it performs operations to connect repositories and logs the process.


---
### handle_github_events 
The `handle_github_events` function processes GitHub repository events such as additions, deletions, and pushes, managing database records and handling repository data accordingly.
- **Inputs**:
    - `installation_id`: A string or None representing the GitHub installation ID, required for added or pushed repositories.
    - `org_id`: A string representing the organization ID associated with the GitHub events.
    - `repos_added`: A list of dictionaries, each representing a repository that has been added.
    - `repos_deleted`: A list of dictionaries, each representing a repository that has been deleted.
    - `repos_pushed`: A list of dictionaries, each representing a repository that has been pushed to.
- **Control Flow**:
    - Check if `installation_id` is None and if there are any added or pushed repositories, raising a ValueError if true.
    - If there are deleted repositories, open a database session and iterate over each deleted repository to find and potentially delete the corresponding primary asset if certain conditions are met.
    - If there are no added or pushed repositories, return early from the function.
    - Attempt to fetch an access token using the `installation_id`, raising an error if unsuccessful.
    - Use a ThreadPoolExecutor to concurrently download and upload each added repository, collecting any errors.
    - Iterate over each pushed repository to download and upload it, collecting any errors.
- **Output**:
    - The function does not return any value; it performs operations such as database updates and repository data handling.


---
### handle_gitlab_events 
The `handle_gitlab_events` function processes GitLab repository events by handling repository additions, deletions, and updates, and manages the corresponding database records and assets.
- **Inputs**:
    - `installation_id`: A string or None representing the GitLab installation ID, required for added or pushed repositories.
    - `org_id`: A string representing the organization ID associated with the repositories.
    - `repos_added`: A list of dictionaries, each representing a repository that has been added.
    - `repos_deleted`: A list of dictionaries, each representing a repository that has been deleted.
    - `repos_pushed`: A list of dictionaries, each representing a repository that has been pushed to.
- **Control Flow**:
    - Check if `installation_id` is None and if there are any added or pushed repositories, raise a ValueError if true.
    - If there are deleted repositories, open a database session and iterate over each deleted repository.
    - For each deleted repository, attempt to find the corresponding primary asset in the database.
    - If the primary asset is found and all its versions have certain statuses, delete the primary asset; otherwise, log a message and skip deletion.
    - If there are no added or pushed repositories, return early from the function.
    - Attempt to fetch an access token using the `installation_id`; if unsuccessful, log an error and raise an exception.
    - Use a ThreadPoolExecutor to concurrently process added repositories by downloading and uploading them using the fetched token.
    - Iterate over pushed repositories and process each one by downloading and uploading it, appending any errors to a list.
- **Output**:
    - The function does not return any value; it performs operations and may raise exceptions if errors occur.


---
### run_codebase_connection 
The `run_codebase_connection` function downloads a codebase from a presigned URL, processes it, and uploads it to an S3 bucket while updating the database with the codebase's metadata.
- **Inputs**:
    - `presigned_url`: A string representing the presigned URL from which the codebase is downloaded.
    - `provisional_codebase_name`: A string representing the provisional name of the codebase to be used for the download destination.
    - `org_id`: A string representing the organization ID, used to verify the version's association with the organization.
    - `version_id`: A string representing the version ID of the codebase.
    - `provider`: An optional string representing the provider of the codebase, defaulting to 'manual'.
- **Control Flow**:
    - The function begins by importing necessary modules and setting up the download destination using the provisional codebase name.
    - It downloads the codebase from the provided presigned URL to the specified destination.
    - Depending on the provider, it may override the codebase name to remove hash values.
    - A temporary directory is created to unpack the downloaded archive, and the codebase is extracted to this directory.
    - The function loads any driverignore files to determine which files should be ignored during processing.
    - A database session is initiated to update the primary asset's display name and check for integrity errors.
    - If an integrity error occurs, the function updates the version status to CONNECTION_FAILED and exits.
    - The function creates an S3 bucket if it doesn't exist and prepares the destination path for the codebase in S3.
    - It iterates over the extracted files, collecting statistics and checking if files are analyzable, updating the total analyzable bytes.
    - If no analyzable files are found, the version status is set to CONNECTION_FAILED, and the function exits.
    - The function uploads the codebase to the S3 bucket, including metadata if available.
    - It updates the database with directory and file nodes, including their metadata, and sets the version status to CONNECTED if applicable.
    - If the version status is GENERATING, it triggers a remote inspection function.
    - Finally, it prints a completion message with the codebase and version details.
- **Output**:
    - The function returns None, as its primary purpose is to perform operations and update the database and S3 storage.


