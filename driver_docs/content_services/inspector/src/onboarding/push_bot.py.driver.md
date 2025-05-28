# Purpose
This Python script is designed to facilitate the automated management and deployment of documentation files to version control repositories, specifically targeting GitHub and GitLab platforms. The script includes several functions that collectively handle the extraction of metadata from pre-signed URLs, execution of shell commands, and the orchestration of asynchronous operations to push documentation updates. The `extract_values_from_presigned_url` function parses URLs to extract key identifiers, while the `run` function executes shell commands, capturing and printing their output. The `push_docs` function is the core component, responsible for downloading documentation archives from an S3 bucket, extracting and synchronizing them with a local repository clone, and then committing and pushing changes to a new branch. This function also handles the creation of pull or merge requests on GitHub or GitLab, depending on the repository's hosting service.

The script is structured to be used as a standalone utility, with functions that interact with external services like AWS S3 for file storage and retrieval, and GitHub/GitLab for version control operations. It imports several modules, including `boto3` for AWS interactions, and uses SQLModel for database operations to retrieve version information. The script is not intended to be a library for importation but rather a script executed to perform specific tasks related to documentation management. It defines a clear public API through its functions, which are designed to be invoked in a sequence to achieve the desired outcome of updating and managing documentation in a version-controlled environment.
# Imports and Dependencies

---
- `os`
- `re`
- `subprocess`
- `uuid`
- `pathlib.Path`
- `urllib.parse.urlparse`
- `hashlib`
- `tempfile`
- `database.db.engine`
- `database.models_v1.GitProviderAppInstallation`
- `onboarding.gh_ops`
- `onboarding.gitlab_ops`
- `onboarding.onboard_utils.unpack_archive_to_finalized_path`
- `sqlmodel.Session`
- `sqlmodel.select`
- `utils.db.get_version_by_id`
- `shutil`
- `boto3`


# Functions

---
### build_s3_path
The function `build_s3_path` constructs an S3 path for a driver documentation ZIP file based on organization ID hash, primary asset ID, and version ID.
- **Inputs**:
    - `org_id_hash`: A string representing the hashed organization ID, used to uniquely identify the organization in the S3 path.
    - `primary_asset_id`: A string representing the primary asset ID, used to identify the specific asset in the S3 path.
    - `version_id`: A string representing the version ID, used to specify the version of the asset in the S3 path.
- **Control Flow**:
    - The function takes three string inputs: `org_id_hash`, `primary_asset_id`, and `version_id`.
    - It constructs a string that represents the S3 path by formatting these inputs into a predefined path structure.
    - The path structure is 'driver_docs/{org_id_hash}/{primary_asset_id}/{version_id}/driver_docs.zip'.
    - The function returns this constructed path as a string.
- **Output**:
    - A string representing the constructed S3 path for the driver documentation ZIP file.


---
### download_file_from_s3
The function `download_file_from_s3` downloads a file from an S3 bucket to a local path and returns the file's metadata.
- **Inputs**:
    - `bucket_name`: The name of the S3 bucket from which the file will be downloaded.
    - `object_key`: The key (path) of the object in the S3 bucket to be downloaded.
    - `local_file_path`: The local file path where the downloaded file will be saved.
- **Control Flow**:
    - Import the `boto3` library to interact with AWS S3.
    - Create an S3 client using `boto3.client('s3')`.
    - Use the `head_object` method of the S3 client to retrieve metadata of the specified object in the bucket.
    - Extract the 'Metadata' from the response and print it.
    - Download the file from the S3 bucket to the specified local path using `s3.download_file`.
    - Print a confirmation message indicating the successful download of the file.
- **Output**:
    - A dictionary containing the metadata of the downloaded file.


---
### extract_values_from_presigned_url
The function `extract_values_from_presigned_url` extracts specific components from a presigned URL path that follows a predefined structure.
- **Inputs**:
    - `url`: A string representing the presigned URL from which values are to be extracted.
- **Control Flow**:
    - Parse the input URL using `urlparse` to extract the path component.
    - Strip leading and trailing slashes from the path.
    - Define a regex pattern to match the expected URL path structure: `driver_docs/<primary_asset_id>/<version_id>/<filename>.zip`.
    - Use `re.match` to match the path against the regex pattern.
    - If the path does not match the pattern, raise a `ValueError`.
    - Extract `primary_asset_id`, `version_id`, and `filename` from the matched groups.
- **Output**:
    - A dictionary containing the extracted values: `primary_asset_id`, `version_id`, and `filename`.


---
### push_docs
The `push_docs` function asynchronously downloads, extracts, and pushes technical documentation to a Git repository, creating a pull or merge request if necessary.
- **Inputs**:
    - `version_id`: A UUID representing the version of the documentation to be processed.
- **Control Flow**:
    - Retrieve the version details from the database using the provided `version_id`.
    - Calculate a hash of the organization ID for use in S3 operations.
    - Determine if the repository is hosted on GitHub or another Git provider based on the presence of an installation ID.
    - Create temporary directories and files to handle the downloaded documentation archive.
    - Download the documentation archive from S3 using the calculated object key and extract it to a temporary directory.
    - Generate a branch name based on the version's display name and prepare the repository URL and access token based on the Git provider.
    - Clone the repository to a temporary directory if it does not already exist.
    - Check out a new branch for the documentation update.
    - Synchronize the extracted documentation to the repository's `driver_docs` directory.
    - Configure Git user details for committing changes.
    - Add the changes to the Git index and check for any differences to commit.
    - If changes exist, commit them with a generated message and push the branch to the remote repository.
    - Create a pull request on GitHub or a merge request on another Git provider if changes were pushed.
- **Output**:
    - The function does not return any value; it performs operations to update documentation in a Git repository and may print status messages to the console.


---
### run
The `run` function executes a shell command in a subprocess, optionally checking for errors, and returns the result.
- **Inputs**:
    - `cmd`: A string representing the shell command to be executed.
    - `cwd`: An optional string specifying the working directory in which to execute the command; defaults to None.
    - `check`: A boolean indicating whether to raise an exception if the command exits with a non-zero status; defaults to True.
- **Control Flow**:
    - The function prints the command to be executed.
    - It calls `subprocess.run` with the provided command, capturing both stdout and stderr, and executes it in the specified working directory if provided.
    - If there is any output in stdout, it is printed.
    - If there is any output in stderr, it is printed.
    - If `check` is True and the command's return code is non-zero, a `subprocess.CalledProcessError` is raised.
    - The function returns the `CompletedProcess` instance containing the execution result.
- **Output**:
    - A `subprocess.CompletedProcess` object containing information about the executed command, including its return code, stdout, and stderr.


---
### sync_directory
The `sync_directory` function synchronizes the contents of a source directory to a destination directory by replacing the destination with the source.
- **Inputs**:
    - `src`: The path to the source directory whose contents are to be copied.
    - `dest`: The path to the destination directory where the source contents will be copied to.
- **Control Flow**:
    - Check if the destination directory exists using `os.path.exists(dest)`.
    - If the destination directory exists, remove it and all its contents using `shutil.rmtree(dest)`.
    - Copy the entire contents of the source directory to the destination directory using `shutil.copytree(src, dest)`.
    - Print a confirmation message indicating that the source directory has been synced to the destination.
- **Output**:
    - The function does not return any value; it performs the side effect of synchronizing the directories and prints a confirmation message.


