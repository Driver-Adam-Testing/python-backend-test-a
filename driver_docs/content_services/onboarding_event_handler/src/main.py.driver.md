# Purpose
This Python file is designed to function as an AWS Lambda handler, primarily focused on processing events from Amazon Simple Notification Service (SNS) that are related to Amazon S3 bucket activities. The core functionality of the code revolves around handling incoming SNS messages, extracting relevant information from S3 event records, and interacting with external services such as AWS Secrets Manager and Auth0 for authentication purposes. The handler function retrieves client credentials from AWS Secrets Manager, obtains a machine-to-machine (M2M) token from Auth0, and processes each S3 event record to determine if it should be onboarded based on specific criteria, such as the presence of allowed tags. If the criteria are met, it generates a presigned URL for the S3 object and sends a request to an onboarding service, using the M2M token for authorization.

The file imports several libraries and modules, including `botocore` for AWS service interactions, `httpx` for HTTP requests, and custom utility functions for S3 operations. It sets up logging configurations to capture and report the processing steps and outcomes. The code is structured to handle multiple records within a single SNS message, ensuring that each S3 event is processed independently. The `exec_onboarding_service` function is responsible for sending the onboarding request to an external API, handling the response, and logging the results. This file is intended to be deployed as a Lambda function, providing a specific and narrow functionality related to S3 event processing and integration with external authentication and onboarding services.
# Imports and Dependencies

---
- `json`
- `logging`
- `os`
- `typing`
- `urllib.parse`
- `botocore`
- `httpx`
- `aws_secretsmanager_caching`
- `src.utils.aws_s3`
- `src.utils.config`


# Global Variables

---
### log_level 
- **Type**: `str`
- **Description**: The `log_level` variable is a string that determines the logging level for the application. It is set by retrieving the `LOG_LEVEL` environment variable, converting it to uppercase, and defaults to `logging.INFO` if the environment variable is not set.
- **Use**: This variable is used to configure the logging level for the application's logger, affecting the verbosity of log messages.


---
### logger 
- **Type**: `logging.Logger`
- **Description**: The `logger` variable is an instance of Python's `logging.Logger` class, configured to handle logging for the application. It is set to the log level specified by the `LOG_LEVEL` environment variable, defaulting to `INFO` if not specified.
- **Use**: This variable is used throughout the code to log informational messages, errors, and debug information, aiding in monitoring and debugging the application's execution.


# Functions

---
### exec_onboarding_service 
The `exec_onboarding_service` function sends an HTTP POST request to an onboarding service with a given event payload and authorization token, and returns the response.
- **Inputs**:
    - `event`: A dictionary containing the event data to be sent as the payload in the HTTP POST request.
    - `token`: A string representing the authorization token to be included in the request headers.
- **Control Flow**:
    - A new HTTP client is created using `httpx.Client` with the base URL from settings and redirects enabled.
    - The event dictionary is copied into a new payload dictionary.
    - Debug logging is performed to log the payload.
    - Headers for the HTTP request are set, including 'Accept', 'Content-Type', and 'Authorization' with the provided token.
    - An HTTP POST request is made to the '/onboarding/' endpoint with the headers and JSON payload.
    - The response is checked for HTTP errors using `raise_for_status`, which will raise an exception for any 4XX or 5XX status codes.
    - The JSON content of the response is extracted and logged as info.
    - The JSON response is returned as the function's output.
- **Output**:
    - A dictionary containing the JSON response from the onboarding service.


---
### handler 
The `handler` function processes SNS messages containing S3 event records, retrieves necessary secrets, and initiates an onboarding process for each S3 object if certain conditions are met.
- **Inputs**:
    - `event`: A dictionary containing the SNS event data, which includes records of S3 events.
    - `context`: An object providing runtime information to the handler, typically not used directly in this function.
- **Control Flow**:
    - Iterates over each record in the 'Records' list of the event dictionary.
    - Parses the SNS message from each record to extract S3 event details.
    - Creates a Secrets Manager client and retrieves client ID and secret from AWS Secrets Manager unless running in a local environment.
    - Constructs a payload for obtaining a machine-to-machine (M2M) token from Auth0.
    - Fetches an M2M token from Auth0 using the constructed payload.
    - Logs the SNS message and the number of S3 records to be processed.
    - Iterates over each S3 record in the SNS message.
    - Extracts bucket name and object key from each S3 record and logs them.
    - Determines if the S3 object should be processed based on GuardDuty tags or environment settings.
    - If processing is allowed, retrieves metadata for the S3 object and generates a presigned URL for downloading the object.
    - Constructs request parameters for the onboarding service if processing is allowed, otherwise logs an error.
    - Creates a request body containing the version ID, processing flag, and request parameters.
    - Calls the `exec_onboarding_service` function to perform the onboarding process and appends the result to the onboarded list.
    - Returns the list of onboarding results.
- **Output**:
    - A list of results from the onboarding service for each processed S3 object.


