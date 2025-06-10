# Purpose
This Python code file provides a focused set of functionalities for interacting with Amazon S3, specifically for generating presigned URLs, retrieving metadata, and checking object tags. It utilizes the `boto3` library, which is the Amazon Web Services (AWS) SDK for Python, to create an S3 client configured with a specific region and an optional custom endpoint URL. The file defines three main functions: `generate_get_presigned_url`, which creates a presigned URL for accessing an S3 object; `head_object`, which retrieves metadata about an S3 object; and `has_allowed_guard_duty_tag`, which checks if an S3 object has a specific tag related to AWS GuardDuty malware scan results.

The code is structured as a utility module, likely intended to be imported and used within a larger application that requires interaction with S3. It does not define a public API or external interface beyond the functions it provides, focusing instead on encapsulating specific S3-related operations. The use of configuration settings for the endpoint URL suggests that the module is designed to be flexible and adaptable to different deployment environments, making it a reusable component within a broader software system.
# Imports and Dependencies

---
- `boto3`
- `src.utils.config`


# Global Variables

---
### s3_client 
- **Type**: `boto3.client`
- **Description**: The `s3_client` is an instance of the boto3 S3 client, which is used to interact with Amazon S3 services. It is configured with a specific region and an optional endpoint URL, which can be customized through the application's settings.
- **Use**: This variable is used to perform various operations on S3, such as generating presigned URLs, retrieving object metadata, and checking object tags.


# Functions

---
### generate_get_presigned_url 
The function generates a presigned URL for accessing an S3 object with a specified expiration time.
- **Inputs**:
    - `bucket`: The name of the S3 bucket where the object is stored.
    - `key`: The key (path) of the object within the S3 bucket.
    - `expires`: The time in seconds for which the presigned URL is valid, defaulting to 3600 seconds (1 hour).
- **Control Flow**:
    - The function calls the `generate_presigned_url` method of the `s3_client` object.
    - It specifies the `ClientMethod` as 'get_object' to indicate the URL is for retrieving an object.
    - It passes the `bucket` and `key` as parameters to identify the specific S3 object.
    - It sets the `ExpiresIn` parameter to the `expires` value to define the URL's validity period.
- **Output**:
    - A string representing the presigned URL that can be used to access the specified S3 object.


---
### has_allowed_guard_duty_tag 
The function checks if an S3 object has a specific tag indicating a safe or unsupported status for GuardDuty malware scanning.
- **Inputs**:
    - `bucket`: The name of the S3 bucket where the object is stored.
    - `key`: The key (path) of the S3 object within the bucket.
- **Control Flow**:
    - Retrieve the tags of the specified S3 object using the `get_object_tagging` method of the S3 client.
    - Define a list of supported tag values: 'NO_THREATS_FOUND' and 'UNSUPPORTED'.
    - Iterate over the tags of the object to check if there is a tag with the key 'GuardDutyMalwareScanStatus' and a value in the supported tags list.
    - Return True if exactly one such tag is found, otherwise return False.
- **Output**:
    - A boolean value indicating whether the S3 object has the 'GuardDutyMalwareScanStatus' tag with a value of 'NO_THREATS_FOUND' or 'UNSUPPORTED'.


---
### head_object 
The `head_object` function retrieves metadata of an object stored in an S3 bucket using the AWS S3 client.
- **Inputs**:
    - `bucket`: A string representing the name of the S3 bucket where the object is stored.
    - `key`: A string representing the key (or path) of the object within the S3 bucket.
- **Control Flow**:
    - The function calls the `head_object` method of the `s3_client` with the specified bucket and key as parameters.
    - The `head_object` method of the S3 client retrieves metadata about the specified object without returning the object itself.
- **Output**:
    - A dictionary containing metadata about the specified S3 object, as returned by the `head_object` method of the S3 client.


