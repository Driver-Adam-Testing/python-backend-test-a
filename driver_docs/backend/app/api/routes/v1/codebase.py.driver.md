# Purpose
This Python file is a FastAPI router module that provides a set of API endpoints for managing and interacting with codebase versions and related operations. The primary functionality includes retrieving available codebase versions, executing codebase analysis, generating codebases, retrieving analysis results, and triggering codebase onboarding. The endpoints are designed to handle HTTP requests and responses, utilizing FastAPI's routing and dependency injection features. The module imports various models and services, such as `PrimaryAsset`, `Version`, and `CodebaseService`, to interact with the database and perform operations related to codebase management.

The file defines several API endpoints using FastAPI's `@router.get` and `@router.post` decorators, each with specific purposes. For instance, the `get_codebase_versions` endpoint retrieves a list of codebase versions for a given codebase ID, supporting pagination through `limit` and `offset` query parameters. The `exec_codebase_analysis` and `exec_codebase_generation` endpoints allow for the execution of codebase analysis and generation tasks, respectively, while ensuring that the user has the necessary permissions. The module also includes mechanisms for handling usage balance checks and raising appropriate HTTP exceptions when conditions are not met. Overall, this file serves as a crucial component in a larger application, providing a structured and secure way to manage codebase-related operations through a RESTful API.
# Imports and Dependencies

---
- `datetime`
- `UUID`
- `modal`
- `UsageEventType`
- `PrimaryAsset`
- `Version`
- `PrimaryAssetKind`
- `VersionStatus`
- `APIRouter`
- `HTTPException`
- `Query`
- `status`
- `JSONResponse`
- `BaseModel`
- `UsageEventMetadata`
- `UsageMetric`
- `UsageSessionMetadata`
- `LLMUsageSession`
- `UsageService`
- `bytes_to_sloc`
- `selectinload`
- `func`
- `select`
- `ContentEditorPermission`
- `ContentReadonlyPermission`
- `UserToken`
- `CurrentSession`
- `settings`
- `CodebaseAnalysisRequest`
- `CodebaseAnalysisResponse`
- `CodebaseAnalysisResult`
- `CodebaseGenerationRequest`
- `CodebaseGenerationResponse`
- `CodebaseOnboardRequest`
- `CodebaseService`


# Global Variables

---
### router 
- **Type**: `APIRouter`
- **Description**: The `router` variable is an instance of FastAPI's `APIRouter` class. It is used to define a group of related API endpoints, which can be included in the main application. This allows for modular and organized routing in a FastAPI application.
- **Use**: The `router` is used to register API endpoints related to codebase operations, such as retrieving versions, executing analysis, generating codebases, and onboarding.


# Classes

---
### CodebaseVersionsResponse 
- **Type**: `class`
- **Members**:
    - `versions`: A list of VersionResponse objects representing the available versions of a codebase.
    - `total_count`: An integer representing the total number of versions available.
    - `limit`: An integer indicating the maximum number of versions to return.
    - `offset`: An integer indicating the starting point for the versions to return.
- **Description**: The CodebaseVersionsResponse class is a Pydantic model that encapsulates the response structure for a request to retrieve codebase versions. It includes a list of version details, the total count of versions, and pagination parameters such as limit and offset to manage the number of versions returned in a single response.
- **Inherits From**:
    - BaseModel


---
### VersionResponse 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the version, represented as a UUID.
    - `version`: A string representing the version of the codebase.
    - `display_name`: An optional string for the display name of the version.
    - `created_at`: A datetime object indicating when the version was created.
- **Description**: The `VersionResponse` class is a data model that represents a response containing information about a specific version of a codebase. It includes attributes such as a unique identifier (`id`), the version string (`version`), an optional display name (`display_name`), and the creation timestamp (`created_at`). This class is used to structure the data returned in API responses related to codebase versions.
- **Inherits From**:
    - BaseModel


# Functions

---
### exec_codebase_analysis 
The `exec_codebase_analysis` function initiates a codebase analysis by calling a service with the user's organization ID and a download URL from the request.
- **Inputs**:
    - `user`: A `UserToken` object representing the authenticated user, which contains the user's organization ID.
    - `request`: A `CodebaseAnalysisRequest` object containing the download URL for the codebase to be analyzed.
- **Control Flow**:
    - The function calls `CodebaseService.execute_codebase_analysis` with the user's organization ID and the download URL from the request.
    - The function directly returns the result of the `execute_codebase_analysis` call.
- **Output**:
    - The function returns a `CodebaseAnalysisResponse` object, which is the result of the codebase analysis execution.


---
### exec_codebase_generation 
The `exec_codebase_generation` function processes codebase versions for a user, ensuring they are valid and within usage limits, and then initiates codebase generation tasks.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to interact with the database.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `request`: A `CodebaseGenerationRequest` object containing the IDs of the codebase versions to be processed.
- **Control Flow**:
    - Constructs a SQL query to select `Version` records joined with `PrimaryAsset` based on the provided version IDs, ensuring they belong to the user's organization and have a status of `CONNECTED`.
    - Executes the query and checks if the number of results matches the number of requested version IDs; raises a 404 HTTPException if not all versions are found.
    - Calculates the total codebase size in bytes by summing the `analyzable_bytes` from each version's metadata.
    - Retrieves the user's usage balance and checks if the total codebase size exceeds the balance; raises a 402 HTTPException if the balance is insufficient.
    - For each version, creates a `UsageSessionMetadata` and initiates an `LLMUsageSession` to log usage metrics, updating the version status to `GENERATING` and committing the changes to the database.
    - Looks up the `inspect_db` function from the `modal` library and spawns a task for each version to initiate the codebase inspection process.
    - Returns a `CodebaseGenerationResponse` with a placeholder call ID.
- **Output**:
    - Returns a `CodebaseGenerationResponse` object containing a call ID, indicating the initiation of the codebase generation process.


---
### get_codebase_analysis 
The `get_codebase_analysis` function retrieves the results of a codebase analysis using a given call ID and raises an error if the analysis status is 'error' or 'expired'.
- **Inputs**:
    - `call_id`: A string representing the unique identifier for the codebase analysis request.
- **Control Flow**:
    - Call the `get_codebase_analysis_results` method of `CodebaseService` with `call_id` to retrieve the analysis response.
    - Check if the `status` of `analysis_response` is either 'error' or 'expired'.
    - If the status is 'error' or 'expired', raise an `HTTPException` with a 400 Bad Request status code.
    - Return the `analysis_response` if no exception is raised.
- **Output**:
    - The function returns a `CodebaseAnalysisResult` object containing the results of the codebase analysis.


---
### get_codebase_versions 
The `get_codebase_versions` function retrieves a paginated list of versions for a specified codebase, ensuring the codebase belongs to the user's organization.
- **Inputs**:
    - `session`: An instance of `CurrentSession` used to execute database queries.
    - `user`: A `UserToken` object representing the authenticated user making the request.
    - `codebase_id`: A `UUID` representing the unique identifier of the codebase for which versions are being requested.
    - `limit`: An integer specifying the maximum number of versions to return, with a default value of 10 and must be greater than 0.
    - `offset`: An integer specifying the number of versions to skip before starting to collect the result set, with a default value of 0 and must be greater than or equal to 0.
- **Control Flow**:
    - The function begins by setting `primary_asset_id` to `codebase_id` and attempts to retrieve the primary asset from the database that matches the given `codebase_id`, belongs to the user's organization, and is of kind `CODEBASE`.
    - If the primary asset is not found, an `HTTPException` with a 404 status code is raised, indicating the codebase was not found.
    - If the primary asset is found, the function constructs a SQL query to select versions associated with the primary asset, ordered by creation date in descending order, and applies the specified `limit` and `offset`.
    - The function executes the query to retrieve the list of versions and also executes another query to count the total number of versions for pagination purposes.
    - A list of `VersionResponse` objects is created from the retrieved versions, each containing the version's ID, display name, and creation date.
    - Finally, the function returns a `CodebaseVersionsResponse` object containing the list of version responses, the total count of versions, and the applied `limit` and `offset`.
- **Output**:
    - The function returns a `CodebaseVersionsResponse` object containing a list of version details, the total count of versions, and pagination information (limit and offset).


---
### trigger_codebase_onboarding 
The function `trigger_codebase_onboarding` initiates the onboarding process for a codebase after verifying the analysis status and available usage balance.
- **Inputs**:
    - `session`: An instance of `CurrentSession` representing the current database session.
    - `user`: An instance of `UserToken` representing the authenticated user making the request.
    - `request`: An instance of `CodebaseOnboardRequest` containing the call ID and codebase object key for the onboarding process.
- **Control Flow**:
    - Retrieve the codebase analysis results using the `request.call_id` from `CodebaseService`.
    - Check if the analysis status is not 'completed'; if so, raise an HTTP 400 Bad Request exception.
    - Extract the `analyzable_sloc` from the analysis results.
    - Retrieve the available usage balance for the user's organization using `UsageService`.
    - Compare `analyzable_sloc` with the available usage balance; if `analyzable_sloc` exceeds the balance, raise an HTTP 400 Bad Request exception.
    - Trigger the codebase onboarding process using `CodebaseService` with the user's organization ID and the codebase object key from the request.
    - Return a JSON response with status code 202 Accepted and a message indicating acceptance.
- **Output**:
    - A `JSONResponse` with status code 202 and a message indicating that the onboarding request has been accepted.


