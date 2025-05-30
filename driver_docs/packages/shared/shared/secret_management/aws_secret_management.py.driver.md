# Purpose
This Python code defines a class `AWSSecretManagementStrategy` that provides a structured approach to managing secrets using AWS Secrets Manager. The class is designed to be initialized with an `AWSClientConfig` object, which contains the necessary AWS credentials and region information. The class offers methods to write, read, and delete secrets in AWS Secrets Manager. The `write_secret` method either updates an existing secret or creates a new one, while the `read_secret` method retrieves and parses the secret value as a JSON object. The `delete_secret` method removes a secret with a specified recovery window. The code also includes a utility function, `format_secret_name`, which formats secret names using a given prefix and suffix.

The file is intended to be used as a library module, providing a specific interface for secret management operations in AWS. It leverages the `boto3` library to interact with AWS services and includes error handling for AWS client errors. The logging module is used to log errors and exceptions, ensuring that issues are recorded for debugging purposes. This code is focused on a narrow functionality, specifically managing secrets in AWS, and is likely to be part of a larger system that requires secure storage and retrieval of sensitive information.
# Imports and Dependencies

---
- `json`
- `logging`
- `boto3`
- `botocore.exceptions.ClientError`
- `shared.interfaces.aws_client_config.AWSClientConfig`


# Global Variables

---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of the `Logger` class from the `logging` module. It is configured to use the module's name as the logger's name, which is typically the name of the file where it is defined. This logger is used to log messages, particularly error and exception messages, throughout the module.
- **Use**: This variable is used to log error and exception messages in the `AWSSecretManagementStrategy` class methods.


# Classes

---
### AWSSecretManagementStrategy 
- **Type**: `class`
- **Members**:
    - `config`: Holds the AWS client configuration details.
    - `client`: Represents the boto3 client for AWS Secrets Manager.
- **Description**: The `AWSSecretManagementStrategy` class provides methods to manage secrets in AWS Secrets Manager. It initializes a boto3 client using the provided AWS client configuration and offers functionality to write, read, and delete secrets. The `write_secret` method either updates an existing secret or creates a new one, while `read_secret` retrieves the secret value if it exists. The `delete_secret` method removes a secret with a specified recovery window.

**Methods**

---
#### AWSSecretManagementStrategy.__init__
The __init__ function initializes an AWSSecretManagementStrategy object by setting up a Boto3 client for AWS Secrets Manager using provided configuration details.
- **Inputs**:
    - `config`: An instance of AWSClientConfig containing AWS configuration details such as region name, access key ID, and secret access key.
- **Control Flow**:
    - The function assigns the provided config object to the instance variable self.config.
    - A new Boto3 session is created using boto3.session.Session().
    - A Boto3 client for the AWS Secrets Manager service is created using the session.client() method, with parameters for service name, region, access key ID, and secret access key extracted from the config object.
    - The created client is assigned to the instance variable self.client.
- **Output**:
    - The function does not return any value; it initializes the instance variables for the AWSSecretManagementStrategy object.


---
#### AWSSecretManagementStrategy.delete_secret
The `delete_secret` function deletes a secret from AWS Secrets Manager with a specified recovery window.
- **Inputs**:
    - `secret_name`: The name of the secret to be deleted from AWS Secrets Manager.
- **Control Flow**:
    - The function calls the `delete_secret` method on the AWS Secrets Manager client, passing the `secret_name` and setting `RecoveryWindowInDays` to 7.
- **Output**:
    - The function does not return any value (returns `None`).


---
#### AWSSecretManagementStrategy.read_secret
The `read_secret` function retrieves a secret from AWS Secrets Manager and returns it as a dictionary if it exists, or logs an error and returns None if it does not.
- **Inputs**:
    - `secret_name`: A string representing the name of the secret to be retrieved from AWS Secrets Manager.
- **Control Flow**:
    - The function attempts to retrieve the secret using the AWS Secrets Manager client with the provided `secret_name`.
    - If the response is empty, it logs an error indicating the secret does not exist and returns None.
    - If the response contains a secret string, it checks if the secret is a string and attempts to parse it as JSON into a dictionary.
    - If the secret is not a string, it directly assigns it to `secret_value`.
    - The function returns the `secret_value` if successful.
    - If a `ClientError` is raised during the process, it logs the exception and returns None.
- **Output**:
    - The function returns a dictionary containing the secret's value if successful, or None if the secret does not exist or an error occurs.


---
#### AWSSecretManagementStrategy.write_secret
The `write_secret` function writes a secret to AWS Secrets Manager, updating it if it exists or creating it if it does not.
- **Inputs**:
    - `secret_name`: The name of the secret to be written or updated in AWS Secrets Manager.
    - `secret_value`: The value of the secret to be stored in AWS Secrets Manager.
- **Control Flow**:
    - The function first calls `read_secret` with `secret_name` to check if the secret already exists.
    - If the secret exists (`value` is truthy), it calls `update_secret` on the AWS Secrets Manager client to update the secret with the new `secret_value`.
    - If the secret does not exist (`value` is falsy), it calls `create_secret` on the AWS Secrets Manager client to create a new secret with the given `secret_name` and `secret_value`.
    - After attempting to write the secret, it checks if the `response` is falsy, indicating a failure in writing the secret.
    - If writing the secret fails, it logs an error message and raises an exception.
- **Output**:
    - The function does not return any value, but it raises an exception if writing the secret fails.



# Functions

---
### format_secret_name 
The function `format_secret_name` concatenates a prefix and suffix with a '/' separator to format a secret name.
- **Inputs**:
    - `prefix`: A string representing the prefix part of the secret name.
    - `suffix`: A string representing the suffix part of the secret name.
- **Control Flow**:
    - The function takes two string inputs, `prefix` and `suffix`.
    - It returns a formatted string by concatenating the `prefix`, a '/', and the `suffix`.
- **Output**:
    - A string that combines the prefix and suffix with a '/' in between, representing a formatted secret name.


