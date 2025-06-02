# Purpose
This Python file is a comprehensive utility module designed to handle various operations related to file processing, storage, and analysis, particularly in the context of managing codebases. It provides a broad range of functionalities, including file type determination, S3 bucket management, file downloading and uploading, archive unpacking, and file encoding analysis. The code is structured to support operations on codebases, such as setting codebase statuses in a database, managing file storage on AWS S3, and processing files for analysis and upload. It includes functions for handling file encoding, checking for binary files, and evaluating file characteristics like size and type.

The module is intended to be used as a library, providing a set of public APIs for interacting with file systems and cloud storage. It integrates with external services like AWS S3 and databases, using libraries such as `boto3`, `requests`, and `sqlmodel`. The code is organized into functions that perform specific tasks, such as `download_file_from_s3`, `upload_file_to_s3`, and `unpack_archive`, which are essential for managing codebase files. Additionally, it includes error handling and logging to ensure robust operation. The module is designed to be imported and used in larger applications that require automated file management and processing capabilities, particularly in environments that involve cloud storage and codebase analysis.
# Imports and Dependencies

---
- `hashlib`
- `os`
- `re`
- `shutil`
- `time`
- `zipfile`
- `collections.abc`
- `concurrent.futures`
- `enum`
- `functools`
- `pathlib`
- `urllib.parse`
- `uuid`
- `requests`
- `boto3`
- `botocore.client`
- `database.models_v2`
- `gitignore_parser`
- `sqlmodel`
- `yaml`
- `chardet`


# Classes

---
### AccessTokenError 
- **Type**: `class`
- **Description**: The `AccessTokenError` class is a custom exception that inherits from the built-in `Exception` class. It is used to represent errors related to access tokens, providing a specific exception type that can be caught and handled separately from other exceptions.
- **Inherits From**:
    - Exception


---
### RunInProgressError 
- **Type**: `class`
- **Description**: The `RunInProgressError` class is a custom exception that inherits from the built-in `Exception` class. It is used to signal that a run is currently in progress, although the class itself does not contain any additional functionality or attributes beyond what is provided by the base `Exception` class.
- **Inherits From**:
    - Exception


# Functions

---
### _wanted_members 
The function `_wanted_members` filters out unwanted members from a zip file, specifically excluding those that start with '__MACOSX'.
- **Inputs**:
    - `zf`: A `zipfile.ZipFile` object representing the zip file from which members are to be filtered.
- **Control Flow**:
    - The function uses a list comprehension to iterate over all members of the zip file obtained via `zf.namelist()`.
    - For each member, it checks if the member's name does not start with the string '__MACOSX'.
    - Only members that do not start with '__MACOSX' are included in the resulting list.
- **Output**:
    - A list of strings, each representing a member of the zip file that does not start with '__MACOSX'.


---
### analyze_binary_file 
The `analyze_binary_file` function analyzes a binary file and returns a dictionary with its size, extension, and binary status.
- **Inputs**:
    - `filepath`: A `Path` object representing the path to the binary file to be analyzed.
- **Control Flow**:
    - The function retrieves the size of the file using `os.path.getsize(filepath)`.
    - It sets the source lines of code (`sloc`) to 0, as binary files do not have lines of code in the traditional sense.
    - The file extension is extracted using `filepath.suffix`.
    - The function sets `is_binary` to `True` to indicate that the file is binary.
    - It sets `is_hex` to `False`, assuming the file is not a hexadecimal file.
- **Output**:
    - A dictionary containing the file's size, source lines of code (sloc), extension, binary status, and hexadecimal status.


---
### analyze_text_file 
The `analyze_text_file` function analyzes a text file to determine its size, source lines of code (SLOC), file extension, and whether it is a hexadecimal file.
- **Inputs**:
    - `filepath`: A `Path` object representing the path to the text file to be analyzed.
- **Control Flow**:
    - Call the `evaluate_file_hex` function to determine if the file is a hexadecimal file.
    - Open the file and calculate the number of lines (SLOC) by iterating over each line in the file.
    - Return a dictionary containing the file's size, SLOC, extension, and flags indicating if it is binary or hexadecimal.
- **Output**:
    - A dictionary with keys 'size', 'sloc', 'extension', 'is_binary', and 'is_hex', providing details about the file's size, source lines of code, extension, and whether it is binary or hexadecimal.


---
### clean_extracted_codebase 
The `clean_extracted_codebase` function removes unwanted files and directories from a codebase directory based on specified patterns.
- **Inputs**:
    - `codebase_root`: A `Path` object representing the root directory of the codebase to be cleaned.
    - `extra_filters`: An optional iterable of strings representing additional glob patterns to filter files and directories for removal.
- **Control Flow**:
    - Initialize a list of default patterns to remove, specifically targeting macOS system files like `__MACOSX` and `.DS_Store`.
    - Check if `extra_filters` is provided, and if so, extend the default patterns with these additional filters.
    - Iterate over each pattern in the combined list of patterns.
    - For each pattern, use `codebase_root.glob(pattern)` to find matching paths.
    - For each matching path, check if it is a directory; if so, remove it using `shutil.rmtree`.
    - If the matching path is a file, remove it using `path.unlink(missing_ok=True)`.
- **Output**:
    - The function does not return any value; it performs in-place cleaning of the specified codebase directory.


---
### create_base_storage_url 
The function `create_base_storage_url` generates a base URL for an S3 bucket using a hashed version of the organization ID.
- **Inputs**:
    - `org_id`: A string representing the organization ID, which is used to generate a unique hashed identifier for the S3 bucket URL.
- **Control Flow**:
    - The function takes the input `org_id` and encodes it to bytes.
    - It then computes the SHA-256 hash of the encoded `org_id`.
    - The hash is converted to a hexadecimal string and truncated to the first 63 characters.
    - A formatted string is returned, which constructs the S3 URL using the truncated hash.
- **Output**:
    - A string representing the base URL for an S3 bucket, formatted as 'https://<hashed_org_id>.s3.amazonaws.com'.


---
### create_bucket_if_dne 
The function `create_bucket_if_dne` checks if an S3 bucket exists and creates it if it does not.
- **Inputs**:
    - `bucket_name`: A string representing the name of the S3 bucket to check and potentially create.
- **Control Flow**:
    - The function attempts to access the specified S3 bucket using the `head_bucket` method to check its existence.
    - If a `ClientError` is raised, indicating the bucket does not exist, the function proceeds to create the bucket using the `create_bucket` method.
    - A message is printed to the console indicating that the bucket has been created.
- **Output**:
    - The function does not return any value; it performs actions to ensure the bucket exists.


---
### delete_file_from_s3 
The `delete_file_from_s3` function deletes a specified file from an Amazon S3 bucket using the boto3 client.
- **Inputs**:
    - `bucket`: A string representing the name of the S3 bucket from which the file will be deleted.
    - `key`: A string representing the key (path) of the file to be deleted within the S3 bucket.
- **Control Flow**:
    - The function imports the boto3 library to interact with AWS services.
    - A boto3 S3 client is instantiated with the region set to 'us-east-1' and AWS credentials retrieved from environment variables.
    - The `delete_object` method of the S3 client is called with the specified bucket and key to delete the file from S3.
- **Output**:
    - The function does not return any value; it performs the deletion operation on the specified S3 object.


---
### download_file_from_presigned_url 
The function downloads a file from a given presigned URL and saves it to a specified local path.
- **Inputs**:
    - `presigned_url`: A string representing the presigned URL from which the file will be downloaded.
    - `download_destination`: A Path object representing the local file path where the downloaded file will be saved.
- **Control Flow**:
    - The function initiates a GET request to the provided presigned URL with streaming enabled.
    - It checks the response status and raises an exception if the request was unsuccessful.
    - It opens the specified download destination file in binary write mode.
    - It iterates over the content of the response in chunks of 8192 bytes and writes each chunk to the file.
- **Output**:
    - The function does not return any value; it performs the side effect of downloading a file to the specified path.


---
### download_file_from_s3 
The function downloads a file from an S3 bucket to a specified local destination.
- **Inputs**:
    - `bucket_name`: The name of the S3 bucket from which the file will be downloaded.
    - `org_id`: The organization ID used as part of the file path in the S3 bucket.
    - `file_name`: The name of the file to be downloaded from the S3 bucket.
    - `download_destination`: The local path where the downloaded file will be saved.
- **Control Flow**:
    - Set the S3 file prefix to 'codebases'.
    - Create an S3 resource using the endpoint URL from the environment variable 'AWS_S3_ENDPOINT_URL'.
    - Access the specified S3 bucket using the provided bucket name.
    - Construct the full S3 path to the file using the prefix, organization ID, and file name.
    - Set the download destination to the local path specified by 'file_name'.
    - Attempt to download the file from the S3 bucket to the local destination.
    - If an exception occurs during download, raise the exception.
- **Output**:
    - The function does not return any value; it performs the side effect of downloading a file to the local file system.


---
### evaluate_file_binary 
The `evaluate_file_binary` function determines if a given file is binary by analyzing its byte content and encoding.
- **Inputs**:
    - `filepath`: A `Path` object representing the path to the file to be evaluated.
- **Control Flow**:
    - The function opens the file in binary read mode and reads its content into `file_bytes`.
    - It checks if any disallowed ASCII control bytes are present in `file_bytes`.
    - If disallowed bytes are found, it attempts to decode the file as UTF-16 (both little-endian and big-endian) to check if it is a text file.
    - If UTF-16 decoding is successful, it uses `chardet` to detect the encoding of the file and checks the confidence level.
    - If the detected encoding is UTF-16 with high confidence, the file is considered not binary; otherwise, it is considered binary.
    - If disallowed bytes are not found, it attempts to decode the file as UTF-8.
    - If UTF-8 decoding is successful, the file is considered not binary.
    - If UTF-8 decoding fails, it uses `chardet` to detect non-ASCII encoding and determines if the file is binary based on the presence of a valid encoding.
- **Output**:
    - A boolean value indicating whether the file is binary (`True`) or not (`False`).


---
### evaluate_file_hex 
The `evaluate_file_hex` function checks if a file's content is predominantly hexadecimal characters.
- **Inputs**:
    - `filepath`: A `Path` object representing the path to the file to be evaluated.
- **Control Flow**:
    - Set a threshold for the percentage of hexadecimal characters required to consider the file as hex (0.99).
    - Define a regular expression pattern to match hexadecimal characters, newlines, and spaces.
    - Initialize a boolean variable `is_hex` to `False`.
    - Open the file at the given `filepath` and read its content into `file_str`.
    - If the file is not empty, count the number of characters in `file_str` that match the regex pattern.
    - Calculate the ratio of hexadecimal characters to the total number of characters in the file.
    - If this ratio exceeds the threshold, set `is_hex` to `True`.
    - Return the value of `is_hex`.
- **Output**:
    - A boolean value indicating whether the file is predominantly composed of hexadecimal characters.


---
### evaluate_file_size_processable 
The function `evaluate_file_size_processable` checks if a file's size is within a specified range to determine if it is processable.
- **Inputs**:
    - `filepath`: A `Path` object representing the file path of the file to be evaluated.
- **Control Flow**:
    - Initialize `is_proc` to `True` to assume the file is processable by default.
    - Retrieve the file size using `os.path.getsize(filepath)`.
    - Define `min_size` as 0 and `max_size` as 1,000,000,000 bytes (1 GB).
    - Check if the file size is less than `min_size` or greater than `max_size`.
    - If the file size is outside the specified range, set `is_proc` to `False`.
    - Return the value of `is_proc`.
- **Output**:
    - A boolean value indicating whether the file size is within the specified range and thus processable.


---
### finalize_codebase_path 
The `finalize_codebase_path` function renames a given directory path if an override name is provided, otherwise it returns the original path.
- **Inputs**:
    - `extracted_path`: A `Path` object representing the directory path that may be renamed.
    - `override_name`: An optional string representing the new name for the directory; if `None`, no renaming occurs.
- **Control Flow**:
    - Check if `override_name` is provided.
    - If `override_name` is provided, construct a new path by combining the parent directory of `extracted_path` with `override_name`.
    - Rename the directory at `extracted_path` to the new path using `os.rename`.
    - Return the new path if renaming occurred.
    - If `override_name` is not provided, return the original `extracted_path`.
- **Output**:
    - A `Path` object representing the final directory path, either renamed or original.


---
### generate_get_presigned_url 
The `generate_get_presigned_url` function creates a presigned URL for accessing an S3 object with a specified expiration time.
- **Inputs**:
    - `bucket`: The name of the S3 bucket where the object is stored.
    - `key`: The key (path) of the object within the S3 bucket.
    - `expires`: The time in seconds for which the presigned URL is valid, defaulting to 3600 seconds (1 hour).
- **Control Flow**:
    - Import the `boto3` library to interact with AWS services.
    - Create an S3 client using `boto3.client` with the specified region and AWS credentials from environment variables.
    - Generate a presigned URL using the `generate_presigned_url` method of the S3 client, specifying the client method as 'get_object', the bucket and key parameters, and the expiration time.
- **Output**:
    - A string representing the presigned URL that allows access to the specified S3 object for the given expiration time.


---
### get_file_type_from_extension 
The function `get_file_type_from_extension` determines the file type based on a given file extension using a predefined mapping.
- **Inputs**:
    - `extension`: A string representing the file extension for which the file type is to be determined.
- **Control Flow**:
    - Load the extension-to-language mapping using the `load_extension_and_name_mapping` function.
    - Retrieve the file type(s) associated with the given extension from the mapping.
    - Check if the extension is specifically '.h', and if so, return 'Header'.
    - If the file type list is not empty and contains exactly one element, return that element.
    - If none of the conditions are met, return `None`.
- **Output**:
    - The function returns a string representing the file type if it can be determined, or `None` if the file type cannot be determined.


---
### get_file_type_from_filename 
The function `get_file_type_from_filename` retrieves the programming language type associated with a given filename using a predefined mapping.
- **Inputs**:
    - `filename`: A string representing the name of the file for which the programming language type is to be determined.
- **Control Flow**:
    - The function calls `load_extension_and_name_mapping()` to retrieve a mapping of filenames to programming languages.
    - It attempts to get the file type from the `name_map` using the provided `filename`.
    - If a file type is found and it is the only one associated with the filename, it returns that file type.
    - If no file type is found or multiple types are associated with the filename, it returns `None`.
- **Output**:
    - The function returns a string representing the programming language type if exactly one type is associated with the filename, otherwise it returns `None`.


---
### get_non_ascii_file_encoding 
The function `get_non_ascii_file_encoding` attempts to detect and return the encoding of a byte sequence that is not ASCII.
- **Inputs**:
    - `file_bytes`: A byte sequence representing the contents of a file.
- **Control Flow**:
    - The function imports the `chardet` library for encoding detection.
    - It initializes several constants: `chunk_size` for the size of byte chunks, `num_chunks` for the maximum number of chunks to process, and `min_confidence` for the minimum confidence level required for an encoding prediction.
    - The byte sequence is divided into chunks of size `chunk_size`, and only the first `num_chunks` are considered.
    - For each chunk, the function uses `chardet.detect` to predict the encoding and confidence level.
    - If the predicted encoding is not ASCII and the confidence level is above `min_confidence`, it attempts to decode the entire byte sequence with the predicted encoding.
    - If decoding is successful, the predicted encoding is stored in `found_encoding` and the loop breaks; otherwise, a message is printed indicating the failure of the predicted encoding.
    - The function returns the `found_encoding`, which is the detected non-ASCII encoding or `None` if no suitable encoding is found.
- **Output**:
    - The function returns a string representing the detected non-ASCII encoding of the byte sequence, or `None` if no suitable encoding is found.


---
### get_root_nodes_in_archive 
The function `get_root_nodes_in_archive` extracts the root nodes from a ZIP archive, excluding any entries from the '__MACOSX' directory.
- **Inputs**:
    - `zip_file`: A `zipfile.ZipFile` object representing the ZIP archive from which to extract root nodes.
- **Control Flow**:
    - Iterate over each file information object in the ZIP archive using `zip_file.infolist()`.
    - For each file, convert its filename to a `Path` object and extract its parts.
    - Check if the first part of the path is not '__MACOSX' and if the path has only one part (indicating it's a root node).
    - If both conditions are met, add a tuple containing the first part of the path and a boolean indicating if it's a directory to the result list.
- **Output**:
    - A list of tuples, where each tuple contains a string representing the root node's name and a boolean indicating if it is a directory.


---
### has_guard_duty_tag 
The function `has_guard_duty_tag` checks if an S3 object has a specific tag indicating its malware scan status.
- **Inputs**:
    - `bucket`: The name of the S3 bucket where the object is stored.
    - `key`: The key (or path) of the S3 object within the bucket.
- **Control Flow**:
    - Import the boto3 library to interact with AWS S3.
    - Create an S3 client using boto3 with credentials and region specified from environment variables.
    - Retrieve the tags of the specified S3 object using the `get_object_tagging` method.
    - Define a list of supported tag values: 'NO_THREATS_FOUND' and 'UNSUPPORTED'.
    - Iterate over the tags to check if any tag has the key 'GuardDutyMalwareScanStatus' and a value in the supported tags list.
    - Return True if such a tag is found, otherwise return False.
- **Output**:
    - A boolean value indicating whether the S3 object has the 'GuardDutyMalwareScanStatus' tag with a value of 'NO_THREATS_FOUND' or 'UNSUPPORTED'.


---
### is_driverignored 
The function `is_driverignored` checks if a given file or any of its parent directories are ignored based on a provided ignore rule function.
- **Inputs**:
    - `file_path`: A `Path` object representing the file path to be checked against the ignore rules.
    - `driverignore`: A callable function or `None` that determines if a given path should be ignored.
- **Control Flow**:
    - Check if `driverignore` is `None`, and if so, return `False` indicating the file is not ignored.
    - Invoke `driverignore` with `file_path` to check if the file itself is ignored; return `True` if it is.
    - Iterate over each parent directory of `file_path` and invoke `driverignore` to check if any parent directory is ignored; return `True` if any are ignored.
    - Handle `ValueError` exceptions during the parent directory checks, which may occur due to relative path errors, and continue checking other directories.
    - Return `False` if neither the file nor any parent directories are ignored.
- **Output**:
    - A boolean value indicating whether the file or any of its parent directories are ignored.


---
### is_on_blacklist 
The function `is_on_blacklist` checks if a given file path is blacklisted based on directory names, file extensions, or file names.
- **Inputs**:
    - `filepath`: A `Path` object representing the file path to be checked against the blacklist.
- **Control Flow**:
    - Initialize a list of blacklisted directory names, file extensions, and file names.
    - Set a boolean variable `is_blacklisted` to `False`.
    - Check if any part of the file path is in the list of blacklisted directories; if so, set `is_blacklisted` to `True`.
    - Check if the file path is a file and its extension is in the list of blacklisted file extensions; if so, set `is_blacklisted` to `True`.
    - Check if the file path is a file and its name is in the list of blacklisted file names; if so, set `is_blacklisted` to `True`.
    - Return the value of `is_blacklisted`.
- **Output**:
    - A boolean value indicating whether the file path is blacklisted (`True`) or not (`False`).


---
### load_driverignore 
The `load_driverignore` function checks for a '.driverignore' file in a specified directory and returns a callable for parsing it if present.
- **Inputs**:
    - `codebase_root`: A `Path` object representing the root directory of the codebase to check for a '.driverignore' file.
- **Control Flow**:
    - List all files in the directory specified by `codebase_root`.
    - Check if '.driverignore' is present in the list of files.
    - If '.driverignore' is found, parse it using `parse_gitignore` and return the resulting callable.
    - If '.driverignore' is not found, return `None`.
- **Output**:
    - A callable for parsing the '.driverignore' file if it exists, otherwise `None`.


---
### load_extension_and_name_mapping 
The function `load_extension_and_name_mapping` loads language extension and filename mappings from a YAML file into two dictionaries.
- **Inputs**:
    - None
- **Control Flow**:
    - The function imports `defaultdict` from `collections` and `yaml` for YAML file parsing.
    - It opens the file located at `/linguist/languages.yml` and loads its content into `language_dict` using `yaml.safe_load`.
    - Two `defaultdict` objects, `extension_map` and `name_map`, are initialized to store lists of languages associated with each extension and filename, respectively.
    - The function iterates over each language in `language_dict`.
    - For each language, it checks if there are any extensions listed and appends the language to the corresponding list in `extension_map` for each extension.
    - Similarly, it checks for filenames and appends the language to the corresponding list in `name_map` for each filename.
    - Finally, the function returns the `extension_map` and `name_map` dictionaries.
- **Output**:
    - The function returns a tuple containing two dictionaries: `extension_map` and `name_map`, which map file extensions and filenames to lists of languages, respectively.


---
### parse_presigned_url 
The `parse_presigned_url` function extracts the S3 bucket name and object key from a given presigned URL.
- **Inputs**:
    - `url`: A string representing the presigned URL to be parsed.
- **Control Flow**:
    - The function imports `unquote_plus` from `urllib.parse` to handle URL decoding.
    - It uses `urlparse` to parse the input URL into its components.
    - The host and path are extracted from the parsed URL, with the path having its leading slash removed.
    - The function checks if the host contains '.s3.' to determine if the URL is domain-style, extracting the bucket name accordingly.
    - If the host starts with 's3-' or 's3.', it is considered path-style, and the bucket name is extracted from the path.
    - If neither condition is met, a `ValueError` is raised indicating an invalid S3 URL format.
    - The path is decoded using `unquote_plus` to handle any URL-encoded characters.
    - Finally, the function returns a tuple containing the bucket name and the decoded key.
- **Output**:
    - A tuple containing the bucket name and the decoded key extracted from the presigned URL.


---
### process_and_upload_all_files_in_parallel 
The function processes and uploads files from a specified directory to an S3 bucket in parallel using multiple threads.
- **Inputs**:
    - `s3_client`: An S3 client object used to interact with the S3 service.
    - `org_hashed_id`: A string representing the hashed ID of the organization, used as part of the S3 key.
    - `primary_asset_id`: A string representing the primary asset ID, used as part of the S3 key.
    - `version_id`: A string representing the version ID, used as part of the S3 key.
    - `extracted_path`: A Path object representing the directory containing files to be processed and uploaded.
    - `download_dir`: A Path object representing the directory where files are downloaded, used to determine relative paths.
    - `db_node_paths`: A set of strings representing paths of files that should be processed and uploaded.
    - `max_workers`: An integer specifying the maximum number of threads to use for parallel processing, defaulting to 8.
- **Control Flow**:
    - Initialize empty lists for file paths and files to process.
    - Traverse the directory specified by 'extracted_path' to collect all file paths.
    - Create a ThreadPoolExecutor with a specified number of workers (threads).
    - Submit tasks to the executor to process and upload each file using the 'process_and_upload_file' function.
    - Collect results from the futures as they complete, appending successful file paths to the result list.
    - Return the list of successfully processed and uploaded file paths.
- **Output**:
    - A list of Path objects representing the files that were successfully processed and uploaded.


---
### process_and_upload_file 
The function processes a local file by re-encoding it if necessary and uploads it to an S3 bucket if it is listed in the database node paths.
- **Inputs**:
    - `s3_client`: An S3 client object used to interact with the S3 service.
    - `org_hashed_id`: A string representing the hashed ID of the organization, used as the S3 bucket name.
    - `primary_asset_id`: A string representing the primary asset ID, used as part of the S3 key.
    - `version_id`: A string representing the version ID, used as part of the S3 key.
    - `local_path`: A Path object representing the local file path to be processed and uploaded.
    - `download_dir`: A Path object representing the directory from which the local path is relative.
    - `db_node_paths`: A set of strings representing paths that are stored in the database and should be processed.
- **Control Flow**:
    - Calculate the relative path of the local file with respect to the download directory.
    - Check if the relative path is in the set of database node paths.
    - If it is, re-encode the file to UTF-8 if necessary using the `reencode_file` function.
    - Construct the S3 key using the primary asset ID, version ID, and the relative path.
    - Upload the file to the S3 bucket using the S3 client and the constructed S3 key.
    - Print a message indicating the file upload and return the local path.
    - If the relative path is not in the database node paths, return None.
- **Output**:
    - The function returns the local path of the file if it was uploaded to S3, otherwise it returns None.


---
### reencode_file 
The `reencode_file` function attempts to re-encode a file to UTF-8 if it is not already in that encoding.
- **Inputs**:
    - `filepath`: A `Path` object representing the path to the file that needs to be re-encoded.
- **Control Flow**:
    - Initialize `is_utf8` to `False` and `decoded_str` to `None`.
    - Open the file in binary read mode and read its contents into `file_bytes`.
    - Attempt to decode `file_bytes` using UTF-8; if successful, set `is_utf8` to `True`.
    - If the file is not UTF-8 encoded, use `get_non_ascii_file_encoding` to predict the file's encoding.
    - If a valid encoding is found, attempt to decode `file_bytes` using this encoding and store the result in `decoded_str`.
    - If decoding fails, print an error message indicating the failure and the predicted encoding.
    - If `decoded_str` is not `None`, open the file in write mode with UTF-8 encoding and write `decoded_str` back to the file.
    - Print a message indicating the file has been updated to UTF-8.
- **Output**:
    - The function does not return any value; it performs file re-encoding as a side effect.


---
### run_file_stats_and_reencode 
The `run_file_stats_and_reencode` function evaluates a file's processability, reencodes it if necessary, analyzes its content, and returns a dictionary of file statistics.
- **Inputs**:
    - `local_path`: A `Path` object representing the local file path to be processed.
    - `driverignore`: An optional `Callable` that determines if a file should be ignored based on custom rules, or `None` if no such rules are applied.
- **Control Flow**:
    - Evaluate if the file size is processable using `evaluate_file_size_processable`.
    - Determine if the file is binary using `evaluate_file_binary`.
    - Check if the file is on a blacklist using `is_on_blacklist`.
    - Check if the file is ignored by the driver using `is_driverignored`.
    - If the file is not binary, reencode it using `reencode_file` and analyze it with `analyze_text_file`.
    - Set the `is_analyzable` flag based on whether the file is hex, processable, and not blacklisted.
    - If the file is binary, analyze it with `analyze_binary_file` and set `is_analyzable` to `False`.
    - Add `is_blacklisted` and `is_ignored` flags to the file statistics.
    - If the file is analyzable, determine its language using `get_file_type_from_extension` or `get_file_type_from_filename`, defaulting to 'Other' if undetermined.
    - If the file is not analyzable, set the language to 'N/A'.
- **Output**:
    - A dictionary containing file statistics, including size, sloc, extension, binary status, hex status, analyzability, blacklist status, ignore status, and language.


---
### set_codebase_status 
The `set_codebase_status` function updates the status of a codebase version in the database using a given version ID and status.
- **Inputs**:
    - `version_id`: A UUID representing the unique identifier of the codebase version to be updated.
    - `status`: An Enum value representing the new status to be set for the codebase version.
- **Control Flow**:
    - Import the `engine` from the `database.db` module.
    - Open a session with the database using the `Session` context manager and begin a transaction.
    - Retrieve the `Version` object from the database using the provided `version_id`.
    - Update the `status` attribute of the retrieved `Version` object with the provided `status`.
    - Add the updated `Version` object back to the session to mark it for update in the database.
- **Output**:
    - The function does not return any value; it performs an update operation on the database.


---
### unpack_archive 
The `unpack_archive` function extracts the contents of a zip archive to a specified directory, handling cases where the archive contains a single root directory differently from those with multiple root nodes.
- **Inputs**:
    - `archive_path`: A `Path` object representing the file path to the zip archive that needs to be unpacked.
    - `extraction_root`: A `Path` object representing the directory where the contents of the archive should be extracted.
- **Control Flow**:
    - Open the zip archive located at `archive_path` using `zipfile.ZipFile`.
    - Retrieve the root nodes of the archive using the `get_root_nodes_in_archive` function.
    - Check if the archive contains a single root directory by evaluating the length of `root_nodes` and the directory status of the first node.
    - If there is a single root directory, set `target_dir` to the path of this directory within `extraction_root` and extract all members of the archive to `extraction_root`.
    - If there are multiple root nodes, create a new directory named after the archive's stem within `extraction_root`, set `target_dir` to this new directory, and extract all members of the archive to `target_dir`.
    - Return the `target_dir` where the archive contents have been extracted.
- **Output**:
    - A `Path` object representing the directory where the archive contents have been extracted.


---
### unpack_archive_to_finalized_path 
The function unpacks an archive, cleans unwanted files, optionally renames the directory, and returns the final directory path.
- **Inputs**:
    - `archive_path`: The path to the archive file that needs to be unpacked.
    - `extraction_root`: The root directory where the archive will be extracted.
    - `override_codebase_name`: An optional string to rename the extracted directory.
    - `extra_filters`: An optional iterable of strings specifying additional patterns to filter out during cleaning.
- **Control Flow**:
    - Call unpack_archive to extract the archive at archive_path into the extraction_root directory.
    - Call clean_extracted_codebase to remove unwanted files and directories from the extracted content, using extra_filters if provided.
    - Call finalize_codebase_path to optionally rename the extracted directory if override_codebase_name is provided, and determine the final directory path.
    - Return the final directory path.
- **Output**:
    - The function returns a Path object representing the final directory on disk after extraction and cleaning.


---
### upload_file_to_s3 
The function uploads a local file to a specified S3 bucket and returns the S3 destination path.
- **Inputs**:
    - `bucket_name`: The name of the S3 bucket where the file will be uploaded.
    - `destination_root`: The root path in the S3 bucket where the file will be stored.
    - `local_path`: The local file path of the file to be uploaded.
- **Control Flow**:
    - Initialize an S3 resource using the endpoint URL from the environment variable 'AWS_S3_ENDPOINT_URL'.
    - Retrieve the specified S3 bucket using the provided bucket name.
    - Check if the local file exists at the given local path.
    - If the file exists, construct the S3 destination path by combining the destination root and the local path.
    - Upload the file to the S3 bucket at the constructed destination path.
- **Output**:
    - The function returns the S3 destination path where the file was uploaded.


---
### upload_to_s3_with_metadata 
The function uploads a zip file to an S3 bucket with specified metadata.
- **Inputs**:
    - `zip_content`: A bytes object representing the content of the zip file to be uploaded.
    - `metadata`: A dictionary containing metadata to be associated with the uploaded object.
    - `upload_key`: A string representing the key under which the file will be stored in the S3 bucket.
- **Control Flow**:
    - Import the boto3 library to interact with AWS S3.
    - Create an S3 client using boto3.
    - Attempt to upload the zip content to the S3 bucket specified by the environment variable 'DROPZONE_BUCKET_NAME', using the provided upload key, content type, and metadata.
    - If an exception occurs during the upload, print the exception and raise a new exception with a message indicating the failure to upload the codebase version.
- **Output**:
    - The function returns a boolean indicating the success of the upload operation, but the return statement is missing, so it implicitly returns None.


---
### wait_for_guard_duty_tag 
The function `wait_for_guard_duty_tag` polls an S3 object for a specific tag indicating malware scan status until the tag is found or a timeout is reached.
- **Inputs**:
    - `bucket`: The name of the S3 bucket where the object is stored.
    - `key`: The key (path) of the S3 object within the bucket.
    - `timeout`: The maximum time in seconds to wait for the tag to be found, defaulting to 60 seconds.
    - `interval`: The time in seconds between each check for the tag, defaulting to 5 seconds.
- **Control Flow**:
    - Record the current time as the start time for the polling process.
    - Print a message indicating the start of polling for the specified tag on the given S3 object.
    - Enter a loop that continues until the elapsed time since the start time exceeds the specified timeout.
    - Within the loop, call the `has_guard_duty_tag` function to check if the S3 object has the desired tag.
    - If the tag is found, print a success message and return `True`.
    - If the tag is not found, print a message indicating the wait and sleep for the specified interval before retrying.
    - If the loop exits due to timeout, print a timeout message and return `False`.
- **Output**:
    - Returns a boolean indicating whether the desired tag was found before the timeout was reached.


