# Purpose
This Python file provides a set of utility functions for interacting with Amazon S3, specifically focusing on operations such as generating presigned URLs, managing objects, and handling bucket names. The code is structured to facilitate secure and efficient access to S3 resources, leveraging the `boto3` library to interact with AWS services. Key functionalities include generating presigned URLs for both uploading and downloading objects, parsing S3 URLs to extract bucket and key information, and performing operations like copying and deleting S3 objects. The file also includes functions to handle organization-specific operations, such as generating hashed bucket names based on organization IDs and checking the existence of objects within these buckets.

The code is designed to be part of a larger application, as indicated by its reliance on configuration settings imported from an external module. It is not a standalone script but rather a library file intended to be imported and used by other parts of the application. The functions defined here provide a public API for S3 operations, abstracting the complexity of direct S3 interactions and offering a simplified interface for common tasks. The use of settings for configuration and the integration of a logger for tracking operations suggest that this code is intended for use in a production environment where maintainability and traceability are important.
# Imports and Dependencies

---
- `hashlib`
- `urllib.parse`
- `boto3`
- `app.core.config`
- `app.core.logger`


# Global Variables

---
### s3_client 
- **Type**: `boto3.client`
- **Description**: The `s3_client` is an instance of the Boto3 S3 client, configured to interact with Amazon S3 services. It is initialized with specific AWS credentials and endpoint settings, allowing for operations such as generating presigned URLs, copying, deleting, and checking the existence of objects in S3 buckets.
- **Use**: This variable is used to perform various S3 operations such as generating presigned URLs, copying, deleting, and checking the existence of objects in S3 buckets.


# Functions

---
### copy_s3_object 
The `copy_s3_object` function copies an object from one S3 bucket to another using the AWS S3 client.
- **Inputs**:
    - `source_bucket`: The name of the source S3 bucket from which the object will be copied.
    - `source_key`: The key (path) of the object in the source S3 bucket.
    - `dest_bucket`: The name of the destination S3 bucket to which the object will be copied.
    - `dest_key`: The key (path) for the object in the destination S3 bucket.
- **Control Flow**:
    - A dictionary `copy_source` is created with the source bucket and key.
    - The `copy_object` method of the `s3_client` is called with `CopySource`, `Bucket`, `Key`, and `TaggingDirective` parameters to perform the copy operation.
    - A log message is generated to indicate the successful copying of the object from the source to the destination.
- **Output**:
    - The function does not return any value; it performs the copy operation and logs the result.


---
### delete_file_from_s3 
The function deletes a specified file from an Amazon S3 bucket using the boto3 client.
- **Inputs**:
    - `key`: The key (or path) of the file to be deleted in the S3 bucket.
    - `bucket`: The name of the S3 bucket from which the file should be deleted.
- **Control Flow**:
    - The function calls the 'delete_object' method of the 's3_client' with the specified 'Bucket' and 'Key' parameters to delete the file from S3.
    - The response from the 'delete_object' call is printed to the console.
- **Output**:
    - The function does not return any value; it performs a side effect by deleting a file from S3 and printing the response.


---
### dropzone_bucket_name 
The `dropzone_bucket_name` function returns the appropriate S3 bucket name based on the application's configuration settings.
- **Inputs**:
    - None
- **Control Flow**:
    - The function checks the `settings.USE_LEGACY_DROPZONE` configuration value.
    - If `USE_LEGACY_DROPZONE` is `False`, it returns the value of `settings.DROPZONE_BUCKET_NAME`.
    - If `USE_LEGACY_DROPZONE` is `True`, it constructs and returns a bucket name using `settings.ENVIRONMENT` and `settings.AWS_S3_CODE_BUCKET_SUFFIX`.
- **Output**:
    - The function outputs a string representing the S3 bucket name.


---
### generate_get_presigned_url 
The function `generate_get_presigned_url` creates a presigned URL for retrieving an object from an S3 bucket.
- **Inputs**:
    - `key`: A string representing the key of the object in the S3 bucket for which the presigned URL is to be generated.
    - `expires`: An integer representing the time in seconds for which the presigned URL is valid, with a default value of 3600 seconds (1 hour).
- **Control Flow**:
    - Determine the bucket name based on the settings configuration, using either the `DROPZONE_BUCKET_NAME` or a combination of `ENVIRONMENT` and `AWS_S3_CODE_BUCKET_SUFFIX` if `USE_LEGACY_DROPZONE` is true.
    - Call the `generate_presigned_url` method of the `s3_client` with the `ClientMethod` set to 'get_object', passing the determined bucket name and the provided key as parameters, along with the expiration time.
- **Output**:
    - A string containing the presigned URL for accessing the specified object in the S3 bucket.


---
### generate_org_get_presigned_url 
The function generates a presigned URL for accessing an S3 object associated with a specific organization.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization, used to derive the S3 bucket name.
    - `key`: A string representing the key of the object in the S3 bucket.
    - `expires`: An integer representing the time in seconds for which the presigned URL is valid, defaulting to 600 seconds.
- **Control Flow**:
    - Compute the S3 bucket name by hashing the organization_id using SHA-256 and taking the first 63 characters of the hexadecimal digest.
    - Call the s3_client's generate_presigned_url method with 'get_object' as the ClientMethod, passing the computed bucket name and the provided key as parameters, along with the expiration time.
    - Return the generated presigned URL.
- **Output**:
    - A string representing the presigned URL that allows access to the specified S3 object for the given expiration time.


---
### generate_put_presigned_url 
The function generates a presigned URL for uploading an object to an S3 bucket with specified parameters.
- **Inputs**:
    - `key`: A string representing the key (path) of the object to be uploaded to the S3 bucket.
    - `content_type`: A string specifying the MIME type of the object to be uploaded.
    - `metadata`: An optional dictionary containing metadata to be associated with the object; defaults to an empty dictionary if not provided.
    - `expires`: An integer representing the time in seconds for which the presigned URL is valid; defaults to 3600 seconds (1 hour).
- **Control Flow**:
    - Check if the 'metadata' argument is None and initialize it as an empty dictionary if so.
    - Determine the bucket name based on the settings configuration, using either the DROPZONE_BUCKET_NAME or a combination of ENVIRONMENT and AWS_S3_CODE_BUCKET_SUFFIX.
    - Call the 'generate_presigned_url' method of the S3 client with 'put_object' as the client method and the specified parameters, including bucket, key, content type, metadata, and expiration time.
    - Return the generated presigned URL.
- **Output**:
    - A string representing the presigned URL for uploading an object to the specified S3 bucket.


---
### head_org_object 
The `head_org_object` function checks if an object with a specified key exists in an S3 bucket derived from an organization's ID.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization, used to derive the S3 bucket name.
    - `key`: A string representing the key of the object to check for existence in the S3 bucket.
    - `expires`: An integer representing the expiration time in seconds for the operation, defaulting to 600, though it is not used in the function.
- **Control Flow**:
    - Compute the S3 bucket name by hashing the `organization_id` and taking the first 63 characters of the SHA-256 hash.
    - Attempt to retrieve the object's metadata from the S3 bucket using the `head_object` method of the S3 client.
    - If the object exists, return `True`.
    - If a `NoSuchKey` exception is raised, indicating the object does not exist, return `False`.
- **Output**:
    - A boolean value indicating whether the object with the specified key exists in the derived S3 bucket.


---
### org_id_to_hash 
The `org_id_to_hash` function generates a truncated SHA-256 hash of a given organization ID.
- **Inputs**:
    - `organization_id`: A string representing the organization ID to be hashed.
- **Control Flow**:
    - The function encodes the input `organization_id` as a byte sequence.
    - It computes the SHA-256 hash of the encoded byte sequence.
    - The resulting hash is converted to a hexadecimal string representation.
    - The function returns the first 63 characters of the hexadecimal hash string.
- **Output**:
    - A string representing the first 63 characters of the SHA-256 hash of the input organization ID.


---
### parse_presigned_url 
The `parse_presigned_url` function extracts the S3 bucket name and object key from a given presigned URL.
- **Inputs**:
    - `url`: A string representing the presigned URL to be parsed.
- **Control Flow**:
    - The function begins by parsing the input URL using `urlparse` to separate its components.
    - It extracts the host and path from the parsed URL, removing any leading slashes from the path.
    - The function checks if the host contains '.s3.' to determine if the URL is in domain-style format, and extracts the bucket name accordingly.
    - If the host starts with 's3-' or 's3.', it assumes a path-style format and extracts the bucket name from the path, adjusting the path to remove the bucket name.
    - If neither format is detected, a `ValueError` is raised indicating an invalid S3 URL format.
    - The path is then decoded using `unquote_plus` to handle any URL-encoded characters, resulting in the object key.
    - Finally, the function returns a tuple containing the bucket name and the object key.
- **Output**:
    - A tuple containing the bucket name and the object key extracted from the URL.


