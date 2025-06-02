# Purpose
This Python code file defines a utility class, `AWSS3Client`, which provides a set of methods for interacting with Amazon S3, a cloud storage service. The class is designed to facilitate common S3 operations such as creating buckets, generating presigned URLs for secure access to S3 objects, uploading files, and downloading files using presigned URLs. The class constructor requires an `AWSClientConfig` object, which encapsulates the necessary AWS credentials and configuration details, ensuring that the S3 client is properly authenticated and configured for the specified AWS region.

The `AWSS3Client` class includes several key methods: `create_bucket_if_dne` checks for the existence of an S3 bucket and creates it if it does not exist; `generate_get_presigned_url` and `generate_put_presigned_url` generate presigned URLs for retrieving and uploading objects, respectively; `upload_to_s3` and `upload_file_to_s3` handle the uploading of data and files to S3; and `download_file_from_presigned_url` facilitates downloading files from S3 using a presigned URL. Additionally, the utility function `org_id_to_hash` is provided to generate a consistent hash from an organization ID, which can be used as a bucket name or part of a key. This code is structured as a library module intended to be imported and used in other parts of a software system that requires S3 interactions.
# Imports and Dependencies

---
- `hashlib`
- `os`
- `pathlib.Path`
- `boto3`
- `httpx`
- `botocore.exceptions.ClientError`
- `shared.interfaces.aws_client_config.AWSClientConfig`


# Classes

---
### AWSS3Client 
- **Type**: `class`
- **Members**:
    - `aws_config`: Stores the AWS client configuration details.
    - `s3_client`: Holds the boto3 S3 client instance for interacting with AWS S3.
- **Description**: The AWSS3Client class provides a high-level interface for interacting with AWS S3, including creating buckets, generating presigned URLs for GET and PUT operations, uploading files, and downloading files using presigned URLs. It utilizes the boto3 library to manage S3 resources and operations, and it handles AWS credentials and configuration through the AWSClientConfig object. The class also includes methods to ensure a bucket exists before performing operations and to upload files directly to S3 or via presigned URLs.

**Methods**

---
#### AWSS3Client.__init__
The `__init__` function initializes an AWSS3Client instance with AWS configuration and creates an S3 client using boto3.
- **Inputs**:
    - `aws_config`: An instance of AWSClientConfig containing AWS configuration details such as region name, access key ID, and secret access key.
- **Control Flow**:
    - Assigns the provided `aws_config` to the instance variable `self.aws_config`.
    - Creates an S3 client using boto3 with the specified region name, access key ID, and secret access key from `aws_config`, and assigns it to the instance variable `self.s3_client`.
- **Output**:
    - The function does not return any value; it initializes the instance variables for the AWSS3Client object.


---
#### AWSS3Client.create_bucket_if_dne
The `create_bucket_if_dne` function checks for the existence of an S3 bucket and creates it if it does not exist.
- **Inputs**:
    - `bucket_name`: A string representing the name of the S3 bucket to check and potentially create.
- **Control Flow**:
    - The function attempts to access the specified S3 bucket using the `head_bucket` method to check if it exists.
    - If a `ClientError` is raised, indicating the bucket does not exist, the function proceeds to create the bucket using the `create_bucket` method.
    - A message is printed to the console indicating that the bucket has been created.
- **Output**:
    - The function does not return any value; it performs actions to ensure the bucket exists.


---
#### AWSS3Client.download_file_from_presigned_url
The function downloads a file from a given presigned URL and saves it to a specified local path.
- **Inputs**:
    - `presigned_url`: A string representing the presigned URL from which the file will be downloaded.
    - `download_destination`: A Path object representing the local file path where the downloaded file will be saved.
- **Control Flow**:
    - Initiates a streaming GET request to the provided presigned URL using httpx.
    - Checks the response status and raises an error if the request was unsuccessful.
    - Opens the specified download destination file in binary write mode.
    - Iterates over the response content in chunks and writes each chunk to the destination file.
- **Output**:
    - The function does not return any value; it performs the side effect of writing the downloaded file to the specified path.


---
#### AWSS3Client.generate_get_presigned_url
The `generate_get_presigned_url` function creates a pre-signed URL for downloading an object from an S3 bucket.
- **Inputs**:
    - `key`: A string representing the key of the object in the S3 bucket.
    - `bucket`: A string representing the name of the S3 bucket.
    - `expires`: An integer representing the time in seconds for which the pre-signed URL is valid, defaulting to 3600 seconds (1 hour).
- **Control Flow**:
    - The function calls the `generate_presigned_url` method of the `s3_client` object.
    - It specifies the `ClientMethod` as 'get_object' to indicate that the URL is for downloading an object.
    - It passes the `bucket` and `key` as parameters to identify the specific object in the S3 bucket.
    - It sets the `ExpiresIn` parameter to the `expires` value to define the URL's validity period.
    - The function returns the generated pre-signed URL as a string.
- **Output**:
    - A string representing the pre-signed URL for downloading the specified object from the S3 bucket.


---
#### AWSS3Client.generate_put_presigned_url
The `generate_put_presigned_url` function generates a pre-signed URL for uploading an object to an S3 bucket using the PUT method.
- **Inputs**:
    - `key`: A string representing the key (or path) of the object to be uploaded to the S3 bucket.
    - `bucket`: A string representing the name of the S3 bucket where the object will be uploaded.
    - `content_type`: A string specifying the MIME type of the object being uploaded.
    - `metadata`: An optional dictionary containing metadata to be associated with the object.
    - `expires`: An integer representing the time in seconds for which the pre-signed URL is valid, defaulting to 3600 seconds (1 hour).
- **Control Flow**:
    - The function calls the `generate_presigned_url` method of the `s3_client` object.
    - It specifies the `ClientMethod` as 'put_object' to indicate that the URL is for uploading an object.
    - The `Params` dictionary is populated with the bucket name, object key, content type, and optional metadata.
    - The `ExpiresIn` parameter is set to the provided `expires` value, determining the URL's validity duration.
    - The function returns the generated pre-signed URL as a string.
- **Output**:
    - A string representing the pre-signed URL for uploading an object to the specified S3 bucket.


---
#### AWSS3Client.get_presigned_url
The `get_presigned_url` function generates a pre-signed URL for accessing an S3 object using the organization's hashed ID as the bucket name.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization, which will be hashed to form the bucket name.
    - `path`: A string representing the path or key of the object in the S3 bucket for which the pre-signed URL is to be generated.
- **Control Flow**:
    - The function begins by hashing the `organization_id` using SHA-256 and truncating the result to 63 characters to form the bucket name.
    - It then calls the `generate_get_presigned_url` method with the `path` as the key and the hashed organization ID as the bucket name.
    - The `generate_get_presigned_url` method generates and returns a pre-signed URL for accessing the specified S3 object.
- **Output**:
    - A string representing the pre-signed URL for accessing the specified S3 object.


---
#### AWSS3Client.upload_file_to_s3
The `upload_file_to_s3` function uploads a file to an S3 bucket, creating the bucket if it does not exist, and optionally includes metadata and content type.
- **Inputs**:
    - `file_path`: A `Path` object representing the local file path to be uploaded.
    - `bucket`: A string representing the name of the S3 bucket where the file will be uploaded.
    - `upload_key`: A string representing the key (path) under which the file will be stored in the S3 bucket.
    - `metadata`: An optional dictionary containing metadata to be associated with the file in S3.
    - `content_type`: An optional string specifying the content type of the file.
- **Control Flow**:
    - The function first calls `create_bucket_if_dne` to ensure the specified S3 bucket exists, creating it if necessary.
    - An empty dictionary `extra_args` is initialized to hold optional parameters for the upload.
    - If `metadata` is provided, it is added to `extra_args` under the key 'Metadata'.
    - If `content_type` is provided, it is added to `extra_args` under the key 'ContentType'.
    - The `upload_file` method of the `s3_client` is called with the file path, bucket name, upload key, and any extra arguments to perform the file upload.
- **Output**:
    - The function does not return any value; it performs the side effect of uploading a file to an S3 bucket.


---
#### AWSS3Client.upload_to_s3
The `upload_to_s3` function uploads a zip file to an S3 bucket using a pre-signed URL.
- **Inputs**:
    - `zip_content`: A bytes object representing the content of the zip file to be uploaded.
    - `metadata`: A dictionary containing metadata to be associated with the uploaded file.
    - `upload_key`: A string representing the key (path) under which the file will be stored in the S3 bucket.
    - `bucket`: A string representing the name of the S3 bucket where the file will be uploaded.
- **Control Flow**:
    - Call `create_bucket_if_dne` to ensure the specified bucket exists, creating it if necessary.
    - Generate a pre-signed URL for uploading the file using `generate_put_presigned_url`.
    - Print the generated S3 URL for debugging purposes.
    - Check if the URL generation failed, and return `False` if it did.
    - Define headers for the HTTP PUT request, including content type and length.
    - Use `httpx.put` to upload the zip content to the S3 bucket via the pre-signed URL.
    - Raise an exception if the HTTP request fails.
    - Return `True` if the upload was successful (HTTP status code 200), otherwise `False`.
- **Output**:
    - A boolean value indicating whether the upload was successful (True) or not (False).



# Functions

---
### org_id_to_hash 
The function `org_id_to_hash` converts an organization ID into a truncated SHA-256 hash string.
- **Inputs**:
    - `organization_id`: A string representing the organization ID to be hashed.
- **Control Flow**:
    - The function encodes the input `organization_id` as a UTF-8 byte string.
    - It computes the SHA-256 hash of the encoded byte string using the `hashlib` library.
    - The resulting hash is converted to a hexadecimal string representation.
    - The function returns the first 63 characters of the hexadecimal hash string.
- **Output**:
    - A string representing the first 63 characters of the SHA-256 hash of the input organization ID.


