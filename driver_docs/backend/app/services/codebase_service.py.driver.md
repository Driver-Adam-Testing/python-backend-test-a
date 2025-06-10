# Purpose
This Python file is a component of a larger system designed to handle codebase analysis and onboarding processes, likely within a cloud-based environment. The file provides a set of functionalities centered around executing and managing codebase analysis tasks, validating security credentials, and facilitating the onboarding of analyzed codebases. The primary class, `CodebaseService`, offers static methods to execute codebase analysis, retrieve analysis results, and trigger onboarding processes. These methods interact with external services, such as AWS S3 for storage and retrieval of codebase data, and a modal function service for executing analysis tasks. The file also includes security checks to validate presigned URLs and object keys, ensuring that only authorized access is permitted.

The code is structured to be part of a broader application, likely intended to be imported and used by other components within the system. It integrates with external modules and services, such as `modal` for function execution and `app.utils.aws_s3` for AWS S3 operations. The file defines a custom exception, `CodebaseAnalysisAuthException`, to handle authorization errors, and it uses logging to track significant events during the execution of its methods. Overall, this file provides a focused set of functionalities related to codebase analysis and onboarding, with a strong emphasis on security and integration with cloud services.
# Imports and Dependencies

---
- `json`
- `pathlib.Path`
- `modal.Function`
- `modal.functions.FunctionCall`
- `app.core.config.settings`
- `app.core.logger.logger`
- `app.schemas.codebase_schema.CodebaseAnalysisMetrics`
- `app.schemas.codebase_schema.CodebaseAnalysisResponse`
- `app.schemas.codebase_schema.CodebaseAnalysisResult`
- `app.schemas.codebase_schema.ModalFunctionCallResponse`
- `app.utils.aws_s3.copy_s3_object`
- `app.utils.aws_s3.dropzone_bucket_name`
- `app.utils.aws_s3.org_id_to_hash`
- `app.utils.aws_s3.parse_presigned_url`


# Classes

---
### CodebaseAnalysisAuthException 
- **Type**: `class`
- **Description**: The `CodebaseAnalysisAuthException` class is a custom exception that inherits from Python's built-in `Exception` class. It is used to signal authentication or authorization errors specifically related to codebase analysis operations, such as validating presigned URLs or object keys for security purposes.
- **Inherits From**:
    - Exception


---
### CodebaseService 
- **Type**: `class`
- **Members**:
    - `execute_codebase_analysis`: Static method to initiate codebase analysis by validating a presigned URL and spawning a modal function.
    - `get_codebase_analysis_results`: Static method to retrieve the results of a codebase analysis using a call ID.
    - `trigger_codebase_onboarding`: Static method to trigger codebase onboarding by validating and moving the analyzed codebase to a designated folder.
- **Description**: The `CodebaseService` class provides static methods to manage the lifecycle of codebase analysis and onboarding processes. It includes methods to execute a codebase analysis by validating a presigned URL and spawning a modal function, retrieve the results of the analysis, and trigger the onboarding process by moving the analyzed codebase to a specific location. The class ensures security by validating URLs and object keys to prevent unauthorized access.

**Methods**

---
#### CodebaseService.execute_codebase_analysis
The `execute_codebase_analysis` function validates a presigned URL and initiates a codebase analysis by spawning a modal function, returning a response with the call ID and codebase object key.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization requesting the codebase analysis.
    - `download_url`: A string representing the presigned URL for downloading the codebase to be analyzed.
- **Control Flow**:
    - The function begins by validating the presigned URL using `validate_codebase_analysis_presigned_url` to ensure it is authorized for the given organization and purpose.
    - It looks up a modal function named 'run_pre_codebase_analysis' in the 'inspector-v2' environment using `Function.lookup`.
    - The presigned URL is parsed to extract the codebase object key using `parse_presigned_url`.
    - The modal function is spawned with the download URL, creating an instance of the function call.
    - A `CodebaseAnalysisResponse` object is returned, containing the call ID of the spawned function and the codebase object key.
- **Output**:
    - A `CodebaseAnalysisResponse` object containing the call ID of the spawned modal function and the codebase object key.


---
#### CodebaseService.get_codebase_analysis_results
The `get_codebase_analysis_results` function retrieves and processes the results of a codebase analysis based on a given call ID.
- **Inputs**:
    - `call_id`: A string representing the unique identifier for the codebase analysis call.
- **Control Flow**:
    - The function begins by calling `execute_modal_function_call` with the provided `call_id` to obtain a `ModalFunctionCallResponse` object, which contains the status and response of the modal function call.
    - A `CodebaseAnalysisResult` object is instantiated using the `call_id`, the status, and any error from the `modal_response`.
    - The function checks if the `modal_response` status is 'completed'.
    - If the status is 'completed', it creates a `CodebaseAnalysisMetrics` object using the response data from `modal_response` and assigns it to the `result` attribute of the `codebase_analysis_results`.
    - Finally, the function returns the `codebase_analysis_results` object.
- **Output**:
    - The function returns a `CodebaseAnalysisResult` object containing the call ID, status, any error message, and the analysis metrics if the analysis was completed.


---
#### CodebaseService.trigger_codebase_onboarding
The `trigger_codebase_onboarding` function initiates the onboarding process for a codebase by validating and moving the analyzed codebase object to a designated folder in an S3 bucket.
- **Inputs**:
    - `organization_id`: A string representing the unique identifier of the organization.
    - `codebase_object_key`: A string representing the S3 object key of the analyzed codebase.
- **Control Flow**:
    - The function begins by validating the `codebase_object_key` using the `validate_analyzed_codebase_object_key` function to ensure it is authorized for the given `organization_id`.
    - Logs an informational message indicating the start of the codebase onboarding process.
    - Retrieves the name of the S3 bucket using the `dropzone_bucket_name` function.
    - Extracts the real file name from the `codebase_object_key` using the `Path` class.
    - Constructs the destination object key by combining the hashed organization ID and the real file name.
    - Copies the S3 object from its current location to the destination location within the same bucket using the `copy_s3_object` function.
    - Logs an informational message indicating the successful triggering of the codebase onboarding for the specified file and organization.
- **Output**:
    - The function does not return any value (returns `None`).



# Functions

---
### execute_modal_function_call 
The `execute_modal_function_call` function retrieves and processes the result of a modal function call using a given call ID.
- **Inputs**:
    - `call_id`: A string representing the unique identifier of the modal function call to be executed.
- **Control Flow**:
    - Retrieve the function call object using the provided call ID.
    - Initialize a `ModalFunctionCallResponse` object with the call ID, status set to 'pending', and response set to None.
    - Attempt to get the response from the function call with a timeout of 0 seconds.
    - If the response is successfully retrieved, parse it as JSON, update the modal response's status to 'completed', and set the parsed response.
    - If a `TimeoutError` occurs, set the modal response's status to 'running'.
    - If any other exception occurs, set the modal response's status to 'error' and record the exception message as the error.
- **Output**:
    - Returns a `ModalFunctionCallResponse` object containing the call ID, status, response, and any error message if applicable.


---
### validate_analyzed_codebase_object_key 
The function validates whether a given codebase object key is authorized for analysis based on the organization ID.
- **Inputs**:
    - `codebase_object_key`: A string representing the key of the codebase object to be validated.
    - `org_id`: A string representing the organization ID used to validate the codebase object key.
- **Control Flow**:
    - Convert the organization ID to a hash using the `org_id_to_hash` function.
    - Split the `codebase_object_key` by '/' and take the first two parts to form `object_key_parts`.
    - Define `object_key_prefix` as 'analysis'.
    - Check if the `org_hash` is not in `object_key_parts` and `object_key_prefix` is in `object_key_parts`.
    - If the above condition is true, raise a `CodebaseAnalysisAuthException` with the message 'Forbidden'.
- **Output**:
    - The function does not return any value; it raises an exception if the validation fails.


---
### validate_codebase_analysis_presigned_url 
The function validates a presigned URL to ensure it is authorized for codebase analysis by checking the bucket name and object key components.
- **Inputs**:
    - `url`: A string representing the presigned URL to be validated.
    - `object_key_prefix`: A string representing the expected prefix of the object key in the URL.
    - `org_id`: A string representing the organization ID, which is used to verify the object key.
- **Control Flow**:
    - Convert the organization ID to a hash using the `org_id_to_hash` function.
    - Retrieve the valid bucket name using the `dropzone_bucket_name` function.
    - Parse the provided URL to extract the bucket name and object key using the `parse_presigned_url` function.
    - Split the object key into parts and check if the parsed bucket matches the valid bucket, and if both the organization hash and object key prefix are present in the object key parts.
    - If the validation fails, raise a `CodebaseAnalysisAuthException` with the message 'Forbidden'.
- **Output**:
    - The function does not return any value; it raises an exception if the validation fails.


